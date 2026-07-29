"""Deliberate-failure tests: prove the pipeline degrades safely.

Each test injects a fault and asserts the system's response — isolation, atomicity,
idempotency, or graceful abstention.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select

from agentwatch.classify.classifier import classify_text
from agentwatch.classify.provider import LLMResult
from agentwatch.classify.providers.baseline import BaselineProvider
from agentwatch.collectors.base import RawArtifact
from agentwatch.db.base import Base
from agentwatch.db.models import CollectionRun, Incident
from agentwatch.db.session import get_engine, session_scope
from agentwatch.pipeline.collect import collect_all, run_collection
from agentwatch.storage.artifacts import NullArtifactStore


def _fresh_db(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'f.sqlite3'}")
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())


class _GoodSource:
    name = "good"

    def fetch(self, since):
        return [RawArtifact(source="good", source_id="1", url="u", title="t", body="deleted files")]


class _TimeoutSource:
    name = "bad"

    def fetch(self, since):
        raise TimeoutError("source timed out")


def test_collector_timeout_is_isolated(monkeypatch, tmp_path):
    """One source failing records a failed run and does not stop the others."""
    _fresh_db(monkeypatch, tmp_path)
    collect_all(
        [_GoodSource(), _TimeoutSource()],
        datetime(2020, 1, 1, tzinfo=UTC),
        store=NullArtifactStore(),
    )
    with session_scope() as s:
        runs = {r.source: r for r in s.scalars(select(CollectionRun)).all()}
        assert runs["good"].status == "success" and runs["good"].items_new == 1
        assert runs["bad"].status == "failed" and "timed out" in runs["bad"].error


class _FlakyStore:
    """Writes the first artifact, then fails — simulating a storage outage mid-batch."""

    def __init__(self):
        self.calls = 0

    def store(self, artifact):
        self.calls += 1
        if self.calls >= 2:
            raise OSError("artifact storage unavailable")
        return None


class _TwoSource:
    name = "two"

    def fetch(self, since):
        return [
            RawArtifact(source="two", source_id=str(i), url=f"u{i}", title="t", body="deleted")
            for i in range(2)
        ]


def test_storage_failure_midbatch_rolls_back(monkeypatch, tmp_path):
    """If persistence fails partway, the run is atomic: zero incidents committed."""
    _fresh_db(monkeypatch, tmp_path)
    run_collection(_TwoSource(), datetime(2020, 1, 1, tzinfo=UTC), store=_FlakyStore())
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Incident)) == 0
        run = s.scalars(select(CollectionRun)).one()
        assert run.status == "failed"


def test_duplicate_collection_is_idempotent(monkeypatch, tmp_path):
    """Re-collecting the same content inserts nothing new (content-hash dedupe)."""
    _fresh_db(monkeypatch, tmp_path)
    src = _GoodSource()
    run_collection(src, datetime(2020, 1, 1, tzinfo=UTC), store=NullArtifactStore())
    run_collection(src, datetime(2020, 1, 1, tzinfo=UTC), store=NullArtifactStore())
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Incident)) == 1
        runs = s.scalars(select(CollectionRun)).all()
        assert [r.items_new for r in runs] == [1, 0]


def test_malformed_source_text_does_not_crash(monkeypatch, tmp_path):
    """Empty/garbage report text ingests fine and the classifier abstains, not crashes."""
    _fresh_db(monkeypatch, tmp_path)

    class _EmptySource:
        name = "empty"

        def fetch(self, since):
            return [RawArtifact(source="empty", source_id="1", url="u", title="", body="")]

    run_collection(_EmptySource(), datetime(2020, 1, 1, tzinfo=UTC), store=NullArtifactStore())
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Incident)) == 1
    out = classify_text("", BaselineProvider())
    assert out.result.abstained is True


class _CrashingProvider:
    name = "crash"

    def generate(self, system, user):
        return LLMResult(text="<<<not json>>>", model_name="crash")


def test_classifier_bad_output_abstains(monkeypatch, tmp_path):
    """A model returning unparseable output yields an abstention, never a crash."""
    out = classify_text("the agent deleted everything", _CrashingProvider())
    assert out.result.abstained is True
    assert out.result.relevance.value == "insufficient_evidence"
