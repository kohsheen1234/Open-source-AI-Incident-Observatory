from datetime import UTC, datetime

from fastapi.testclient import TestClient

from agentwatch.api.app import create_app
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, Incident, RawArtifact
from agentwatch.db.session import get_engine, session_scope
from dashboard.client import AgentWatchClient


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'd.sqlite3'}")
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
            body="rm -rf",
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


def test_client_raises_apiunavailable_on_error(monkeypatch):
    import pytest

    import dashboard.client as c

    monkeypatch.setattr(c.time, "sleep", lambda *a, **k: None)  # no waiting in tests

    class BadResp:
        def raise_for_status(self):
            raise RuntimeError("502 Bad Gateway (cold start)")

        def json(self):
            return {}

    class BadClient:
        def get(self, *a, **k):
            return BadResp()

    api = c.AgentWatchClient(client=BadClient())
    with pytest.raises(c.APIUnavailable):
        api.stats()


def test_client_reads_and_reviews(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    api = AgentWatchClient(client=TestClient(create_app()))
    page = api.incidents()
    assert page["total"] == 1
    incident_id = page["items"][0]["id"]
    assert api.stats()["total_classified"] == 1
    review = api.review(incident_id, reviewer="me", decision="accept")
    assert review["decision"] == "accept"
