from datetime import UTC, datetime

from agentwatch.collectors.base import DataSource
from agentwatch.db.models import CollectionRun
from agentwatch.db.session import session_scope
from agentwatch.logging import get_logger
from agentwatch.pipeline.ingest import persist_artifacts
from agentwatch.storage.artifacts import ArtifactStore

log = get_logger("collect")


def run_collection(source: DataSource, since: datetime, *, store: ArtifactStore) -> int:
    """Run one source. Ingestion is atomic — if it fails partway, its data is rolled
    back — while the CollectionRun record is written in a separate transaction so the
    failure is always recorded (and other sources are unaffected)."""
    started = datetime.now(UTC)
    with session_scope() as s:
        run = CollectionRun(source=source.name, started_at=started, status="running")
        s.add(run)
        s.flush()
        run_id = run.id

    fetched = new = 0
    status, error = "success", None
    try:
        # Own transaction: on any error, session_scope rolls back all persisted rows.
        with session_scope() as s:
            artifacts = source.fetch(since)
            result = persist_artifacts(s, artifacts, run_id=run_id, store=store)
            fetched, new = result.fetched, result.new
        log.info("collection.success", source=source.name, fetched=fetched, new=new)
    except Exception as exc:  # isolate: record failure, do not propagate
        status, error = "failed", str(exc)
        log.error("collection.failed", source=source.name, error=str(exc))

    with session_scope() as s:
        run = s.get(CollectionRun, run_id)
        run.items_fetched = fetched
        run.items_new = new
        run.status = status
        run.error = error
        run.finished_at = datetime.now(UTC)
    return run_id


def collect_all(sources: list[DataSource], since: datetime, *, store: ArtifactStore) -> list[int]:
    return [run_collection(src, since, store=store) for src in sources]
