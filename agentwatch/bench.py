"""Local load-test harness.

Generates synthetic incidents (with a duplicate fraction), runs them through the real
ingestion and classification pipeline, then measures API latency — all on a throwaway
SQLite database so it costs nothing to run. See `docs/benchmarks.md`.
"""

import os
import resource
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from agentwatch.collectors.base import RawArtifact


@dataclass
class BenchResult:
    count: int
    duplicate_fraction: float
    ingest_seconds: float
    ingest_per_sec: float
    fetched: int
    new: int
    suppressed: int
    suppression_rate: float
    classify_seconds: float
    classify_per_sec: float
    classified: int
    api_p50_ms: float
    api_p95_ms: float
    api_samples: int
    db_bytes: int
    peak_rss_mb: float
    by_incident_type: dict = field(default_factory=dict)


def _synth(count: int, duplicate_fraction: float) -> list[RawArtifact]:
    """Build `count` artifacts; `duplicate_fraction` of them repeat earlier content."""
    uniques = max(1, int(count * (1 - duplicate_fraction)))
    base = datetime(2026, 1, 1, tzinfo=UTC)
    verbs = [
        "deleted the repository with rm -rf",
        "ignored my instruction and kept emailing the client",
        "escalated its own permissions via sudoers",
        "broke out of the sandbox onto the host",
        "lied about running the tests",
        "made a purchase without asking",
        "saved the wrong file, harmless",
        "did something unclear in the logs",
    ]
    out: list[RawArtifact] = []
    for i in range(count):
        src_i = i if i < uniques else i % uniques  # repeats reuse an earlier item verbatim
        out.append(
            RawArtifact(
                source="synthetic",
                source_id=str(src_i),
                url=f"https://example.com/incident/{src_i}",
                title=f"Incident {src_i}: an agent {verbs[src_i % len(verbs)]}",
                body=f"Report #{src_i}. The agent {verbs[src_i % len(verbs)]}. Details follow.",
                author=f"user_{src_i % 500}",
                published_at=base + timedelta(minutes=src_i),
                raw={"i": src_i},
            )
        )
    return out


def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def run_benchmark(
    count: int = 100_000, duplicate_fraction: float = 0.3, chunk: int = 1000
) -> BenchResult:
    # Isolated throwaway SQLite DB so the run is free and repeatable.
    tmpdir = tempfile.mkdtemp(prefix="agentwatch-bench-")
    db_path = os.path.join(tmpdir, "bench.sqlite3")
    os.environ["AGENTWATCH_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"

    from agentwatch.classify.persist import classify_pending
    from agentwatch.classify.providers.baseline import BaselineProvider
    from agentwatch.config import get_settings
    from agentwatch.db.base import Base
    from agentwatch.db.session import get_engine, session_scope
    from agentwatch.pipeline.ingest import persist_artifacts
    from agentwatch.storage.artifacts import NullArtifactStore

    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())

    artifacts = _synth(count, duplicate_fraction)
    store = NullArtifactStore()

    # ---- ingestion ----
    fetched = new = 0
    t0 = time.perf_counter()
    for batch in _chunks(artifacts, chunk):
        with session_scope() as s:
            r = persist_artifacts(s, batch, run_id=None, store=store)
        fetched += r.fetched
        new += r.new
    ingest_seconds = time.perf_counter() - t0
    suppressed = fetched - new

    # ---- classification ----
    provider = BaselineProvider()
    classified = 0
    t0 = time.perf_counter()
    while True:
        with session_scope() as s:
            n = classify_pending(s, provider, limit=chunk)
        classified += n
        if n == 0:
            break
    classify_seconds = time.perf_counter() - t0

    # ---- API latency (in-process; no network) ----
    from fastapi.testclient import TestClient

    from agentwatch.api.app import create_app

    client = TestClient(create_app())
    latencies: list[float] = []
    for _ in range(200):
        t = time.perf_counter()
        client.get("/incidents?limit=50")
        latencies.append((time.perf_counter() - t) * 1000)
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(0.95 * len(latencies)) - 1]

    with session_scope() as s:
        from agentwatch.api import queries

        stats = queries.stats(s)

    db_bytes = os.path.getsize(db_path)
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mb = maxrss / (1024 * 1024) if maxrss > 10_000_000 else maxrss / 1024

    return BenchResult(
        count=count,
        duplicate_fraction=duplicate_fraction,
        ingest_seconds=round(ingest_seconds, 2),
        ingest_per_sec=round(fetched / ingest_seconds, 1) if ingest_seconds else 0.0,
        fetched=fetched,
        new=new,
        suppressed=suppressed,
        suppression_rate=round(suppressed / fetched, 3) if fetched else 0.0,
        classify_seconds=round(classify_seconds, 2),
        classify_per_sec=round(classified / classify_seconds, 1) if classify_seconds else 0.0,
        classified=classified,
        api_p50_ms=round(p50, 2),
        api_p95_ms=round(p95, 2),
        api_samples=len(latencies),
        db_bytes=db_bytes,
        peak_rss_mb=round(peak_rss_mb, 1),
        by_incident_type=stats["by_incident_type"],
    )


def format_report(r: BenchResult) -> str:
    mb = r.db_bytes / (1024 * 1024)
    return "\n".join(
        [
            "AgentWatch local benchmark",
            "==========================",
            f"workload           : {r.count:,} synthetic incidents "
            f"({int(r.duplicate_fraction * 100)}% duplicates)",
            "",
            "Ingestion",
            f"  throughput       : {r.ingest_per_sec:,.0f} records/sec",
            f"  elapsed          : {r.ingest_seconds:.2f} s",
            f"  new / fetched    : {r.new:,} / {r.fetched:,}",
            f"  dedup suppressed : {r.suppressed:,} ({r.suppression_rate:.0%})",
            "",
            "Classification (baseline provider)",
            f"  throughput       : {r.classify_per_sec:,.0f} incidents/sec",
            f"  elapsed          : {r.classify_seconds:.2f} s",
            f"  classified       : {r.classified:,}",
            "",
            "API latency (GET /incidents, in-process, "
            f"{r.api_samples} samples)",
            f"  p50              : {r.api_p50_ms:.2f} ms",
            f"  p95              : {r.api_p95_ms:.2f} ms",
            "",
            "Footprint",
            f"  database size    : {mb:.1f} MB",
            f"  peak memory      : {r.peak_rss_mb:.0f} MB",
        ]
    )
