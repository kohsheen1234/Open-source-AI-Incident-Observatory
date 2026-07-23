from datetime import UTC, datetime

from sqlalchemy import select

from agentwatch.collectors.base import RawArtifact
from agentwatch.db.base import Base
from agentwatch.db.models import CollectionRun
from agentwatch.db.session import get_engine
from agentwatch.pipeline.collect import collect_all
from agentwatch.storage.artifacts import ArtifactStore


class GoodSource:
    name = "good"

    def fetch(self, since):
        return [RawArtifact(source="good", source_id="1", url="u", title="t", body="b")]


class BadSource:
    name = "bad"

    def fetch(self, since):
        raise RuntimeError("boom")


def test_collect_all_isolates_failures(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'c.sqlite3'}")
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())

    ids = collect_all(
        [GoodSource(), BadSource()],
        datetime(2020, 1, 1, tzinfo=UTC),
        store=ArtifactStore(tmp_path),
    )
    assert len(ids) == 2

    from agentwatch.db.session import session_scope

    with session_scope() as s:
        runs = {r.source: r for r in s.scalars(select(CollectionRun)).all()}
    assert runs["good"].status == "success" and runs["good"].items_new == 1
    assert runs["bad"].status == "failed" and "boom" in runs["bad"].error
