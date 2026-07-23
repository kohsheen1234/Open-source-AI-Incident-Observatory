from datetime import UTC, datetime

from agentwatch.collectors.base import RawArtifact
from agentwatch.storage.artifacts import ArtifactStore


def test_store_writes_hashed_json_idempotently(tmp_path):
    store = ArtifactStore(tmp_path)
    art = RawArtifact(
        source="replay",
        source_id="1",
        url="u",
        title="t",
        body="b",
        published_at=datetime(2026, 3, 2, tzinfo=UTC),
    )
    p1 = store.store(art)
    p2 = store.store(art)
    assert p1 == p2
    assert p1.exists()
    assert art.content_hash in p1.name
    assert "replay/2026/03" in str(p1).replace("\\", "/")
    assert sum(1 for _ in tmp_path.rglob("*.json")) == 1
