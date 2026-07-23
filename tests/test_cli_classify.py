from datetime import UTC, datetime

from sqlalchemy import func, select

from agentwatch.cli import run_classify
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, Incident, RawArtifact
from agentwatch.db.session import get_engine, session_scope


def test_run_classify_labels_incidents(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'x.sqlite3'}")
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())

    with session_scope() as s:
        ra = RawArtifact(
            source="replay",
            source_id="1",
            url="u",
            content_hash="h1",
            raw_json={},
            fetched_at=datetime.now(UTC),
        )
        s.add(ra)
        s.flush()
        s.add(
            Incident(
                raw_artifact_id=ra.id,
                source="replay",
                url="u",
                title="t",
                body="the agent deleted my repo with rm -rf",
                ingested_at=datetime.now(UTC),
                content_hash="h1",
            )
        )

    n = run_classify("baseline", limit=None)
    assert n == 1
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Classification)) == 1
