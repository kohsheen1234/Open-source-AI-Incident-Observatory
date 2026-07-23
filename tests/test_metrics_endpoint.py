from datetime import UTC, datetime

from fastapi.testclient import TestClient

from agentwatch.api.app import create_app
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, CollectionRun, Incident, RawArtifact
from agentwatch.db.session import get_engine, session_scope


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'm.sqlite3'}")
    monkeypatch.delenv("AGENTWATCH_API_KEY", raising=False)
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
        inc = Incident(
            raw_artifact_id=ra.id,
            source="replay",
            url="u",
            title="t",
            body="b",
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
                incident_type="deception",
                severity=3,
                confidence=0.7,
                abstained=False,
                created_at=datetime.now(UTC),
            )
        )
        s.add(
            CollectionRun(
                source="replay",
                started_at=datetime.now(UTC),
                status="success",
                items_fetched=1,
                items_new=1,
            )
        )


def test_metrics_endpoint_exposes_prometheus_text(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    resp = TestClient(create_app()).get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "agentwatch_incidents_total 1.0" in body
    assert "agentwatch_classifications_total 1.0" in body
    assert 'agentwatch_incidents_by_type{incident_type="deception"} 1.0' in body
    assert 'agentwatch_collection_runs_total{status="success"} 1.0' in body
