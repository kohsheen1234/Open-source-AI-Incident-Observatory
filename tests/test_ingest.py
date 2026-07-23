from datetime import UTC, datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from agentwatch.collectors.base import RawArtifact
from agentwatch.db.base import Base
from agentwatch.db.models import Incident
from agentwatch.db.models import RawArtifact as RawArtifactRow
from agentwatch.pipeline.ingest import persist_artifacts
from agentwatch.storage.artifacts import ArtifactStore


def _artifacts():
    return [
        RawArtifact(
            source="replay",
            source_id=str(i),
            url=f"u{i}",
            title=f"t{i}",
            body="b",
            author="alice",
            published_at=datetime(2026, 3, 1, tzinfo=UTC),
        )
        for i in range(3)
    ]


def test_persist_is_idempotent_and_hashes_author(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    store = ArtifactStore(tmp_path)

    with Session(engine) as s:
        r1 = persist_artifacts(s, _artifacts(), run_id=None, store=store)
        s.commit()
        assert r1.fetched == 3 and r1.new == 3

        r2 = persist_artifacts(s, _artifacts(), run_id=None, store=store)
        s.commit()
        assert r2.fetched == 3 and r2.new == 0  # dedupe on content hash

    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(RawArtifactRow)) == 3
        incidents = s.scalars(select(Incident)).all()
        assert len(incidents) == 3
        assert all(i.author_hash is not None and "alice" not in i.author_hash for i in incidents)
