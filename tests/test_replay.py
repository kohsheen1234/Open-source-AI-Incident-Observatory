from datetime import UTC, datetime

from agentwatch.collectors.replay import ReplaySource


def test_replay_loads_bundled_fixtures():
    src = ReplaySource()
    arts = src.fetch(since=datetime(2000, 1, 1, tzinfo=UTC))
    assert src.name == "replay"
    assert len(arts) >= 3
    assert all(a.source == "replay" for a in arts)
    assert all(len(a.content_hash) == 64 for a in arts)


def test_replay_filters_by_since():
    src = ReplaySource()
    arts = src.fetch(since=datetime(2026, 3, 10, tzinfo=UTC))
    assert all(a.published_at >= datetime(2026, 3, 10, tzinfo=UTC) for a in arts)
    assert len(arts) < 4
