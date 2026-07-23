from datetime import UTC, datetime

from sqlalchemy import func, select

from agentwatch.cli import run_once
from agentwatch.db.base import Base
from agentwatch.db.models import Incident
from agentwatch.db.session import get_engine


def test_run_once_replay_populates_incidents(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'cli.sqlite3'}")
    monkeypatch.setenv("AGENTWATCH_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())

    run_once("replay", since=datetime(2000, 1, 1, tzinfo=UTC))

    from agentwatch.db.session import session_scope

    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Incident)) >= 3


def test_build_scheduler_registers_job():
    from agentwatch.scheduler import build_scheduler

    scheduler = build_scheduler(interval_minutes=30)
    assert scheduler.get_job("collect") is not None
