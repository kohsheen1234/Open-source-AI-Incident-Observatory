from datetime import UTC, datetime

from sqlalchemy import select

from agentwatch.config import get_settings
from agentwatch.db.base import Base
from agentwatch.db.models import CollectionRun
from agentwatch.db.session import get_engine, session_scope


def test_session_scope_commits(monkeypatch, tmp_path):
    db = tmp_path / "t.sqlite3"
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{db}")
    # get_engine() reads the cached Settings; clear both so the tmp DB is used.
    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())

    with session_scope() as s:
        s.add(CollectionRun(source="hn", started_at=datetime.now(UTC), status="running"))

    with session_scope() as s:
        rows = s.scalars(select(CollectionRun)).all()
        assert len(rows) == 1
        assert rows[0].source == "hn"
