from datetime import UTC, datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from agentwatch.classify.persist import classify_pending
from agentwatch.classify.providers.baseline import BaselineProvider
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, Incident, RawArtifact


def _seed(s):
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
            title="deleted",
            body="the agent deleted my repo with rm -rf",
            ingested_at=datetime.now(UTC),
            content_hash="h1",
        )
    )


def test_classify_pending_writes_one_row_per_incident():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        _seed(s)
        s.commit()
        n = classify_pending(s, BaselineProvider())
        s.commit()
        assert n == 1
        assert classify_pending(s, BaselineProvider()) == 0  # idempotent: nothing pending

    with Session(engine) as s:
        c = s.scalars(select(Classification)).one()
        assert c.incident_type == "destructive_action"
        assert c.model_name == "baseline"
        assert s.scalar(select(func.count()).select_from(Classification)) == 1
