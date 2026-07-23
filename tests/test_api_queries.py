from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from agentwatch.api import queries
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, Incident, RawArtifact


def _engine_with_data():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
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
        inc = Incident(
            raw_artifact_id=ra.id,
            source="replay",
            url="u",
            title="t",
            body="the agent deleted files",
            ingested_at=datetime.now(UTC),
            content_hash="h1",
        )
        s.add(inc)
        s.flush()
        s.add(
            Classification(
                incident_id=inc.id,
                model_name="baseline",
                prompt_version="v1",
                relevance="relevant",
                incident_type="destructive_action",
                severity=4,
                confidence=0.7,
                abstained=False,
                created_at=datetime.now(UTC),
            )
        )
        s.commit()
    return engine


def test_list_and_filter_incidents():
    engine = _engine_with_data()
    with Session(engine) as s:
        rows, total = queries.list_incidents(s)
        assert total == 1
        _, cls = rows[0]
        assert cls.incident_type == "destructive_action"

        _, total_filtered = queries.list_incidents(s, incident_type="deception")
        assert total_filtered == 0


def test_add_review_and_detail():
    engine = _engine_with_data()
    with Session(engine) as s:
        inc_id = queries.list_incidents(s)[0][0][0].id
        review = queries.add_review(s, inc_id, reviewer="me", decision="accept", notes="ok")
        s.commit()
        assert review.decision == "accept"
        inc, classes, reviews = queries.get_incident(s, inc_id)
        assert len(classes) == 1 and len(reviews) == 1


def test_add_review_without_classification_errors():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s, pytest.raises(ValueError):
        queries.add_review(s, 999, reviewer="me", decision="accept", notes=None)


def test_stats_and_csv():
    engine = _engine_with_data()
    with Session(engine) as s:
        st = queries.stats(s)
        assert st["total_incidents"] == 1
        assert st["by_incident_type"]["destructive_action"] == 1
        csv_text = queries.incidents_csv(s)
        assert "destructive_action" in csv_text
        assert csv_text.splitlines()[0].startswith("id,")
