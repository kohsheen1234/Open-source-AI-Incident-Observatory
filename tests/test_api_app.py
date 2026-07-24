from datetime import UTC, datetime

from fastapi.testclient import TestClient

from agentwatch.api.app import create_app
from agentwatch.db.base import Base
from agentwatch.db.models import Classification, Incident, RawArtifact
from agentwatch.db.session import get_engine, session_scope


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'api.sqlite3'}")
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
            url="http://x/1",
            title="agent deleted files",
            body="rm -rf happened",
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


def test_health_and_list_and_review_and_csv(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    client = TestClient(create_app())

    assert client.get("/health").json()["status"] == "ok"

    page = client.get("/incidents").json()
    assert page["total"] == 1
    incident_id = page["items"][0]["id"]
    assert page["items"][0]["classification"]["incident_type"] == "destructive_action"

    detail = client.get(f"/incidents/{incident_id}").json()
    assert detail["body"] == "rm -rf happened"

    r = client.post(
        f"/incidents/{incident_id}/review", json={"reviewer": "me", "decision": "accept"}
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "accept"

    stats = client.get("/stats").json()
    assert stats["total_classified"] == 1

    csv_resp = client.get("/exports/incidents.csv")
    assert csv_resp.status_code == 200
    assert "destructive_action" in csv_resp.text


def test_cors_header_present(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    client = TestClient(create_app())
    r = client.get("/stats", headers={"Origin": "https://example.com"})
    assert r.headers.get("access-control-allow-origin") == "*"


def test_missing_incident_returns_404(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    client = TestClient(create_app())
    assert client.get("/incidents/999").status_code == 404


def test_write_requires_key_when_configured(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path)
    monkeypatch.setenv("AGENTWATCH_API_KEY", "secret")
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    client = TestClient(create_app())
    incident_id = client.get("/incidents").json()["items"][0]["id"]
    denied = client.post(
        f"/incidents/{incident_id}/review", json={"reviewer": "me", "decision": "accept"}
    )
    assert denied.status_code == 401
    ok = client.post(
        f"/incidents/{incident_id}/review",
        headers={"X-API-Key": "secret"},
        json={"reviewer": "me", "decision": "accept"},
    )
    assert ok.status_code == 200
