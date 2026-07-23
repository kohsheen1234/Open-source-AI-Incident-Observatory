from datetime import UTC, datetime

from agentwatch.collectors.base import DataSource, RawArtifact


def test_raw_artifact_content_hash_stable():
    art = RawArtifact(source="hn", source_id="1", url="u", title="t", body="b")
    assert len(art.content_hash) == 64
    same = RawArtifact(source="hn", source_id="1", url="u", title="t", body="b", raw={"x": 1})
    assert art.content_hash == same.content_hash  # raw payload does not affect the hash


def test_datasource_protocol_is_satisfied():
    class Dummy:
        name = "dummy"

        def fetch(self, since: datetime) -> list[RawArtifact]:
            return []

    d: DataSource = Dummy()
    assert d.fetch(datetime.now(UTC)) == []
