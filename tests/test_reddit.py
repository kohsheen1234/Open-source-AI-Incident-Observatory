from datetime import UTC, datetime
from types import SimpleNamespace

from agentwatch.collectors.reddit import RedditSource, reddit_enabled


def test_reddit_disabled_without_creds(monkeypatch):
    monkeypatch.delenv("AGENTWATCH_REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("AGENTWATCH_REDDIT_CLIENT_SECRET", raising=False)
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    assert reddit_enabled() is False


def test_maps_submissions_to_artifacts():
    submission = SimpleNamespace(
        id="abc",
        title="Agent escalated its own permissions",
        selftext="It edited the sudoers file to keep running.",
        author=SimpleNamespace(name="redditor1"),
        created_utc=1_700_000_000.0,
        permalink="/r/x/comments/abc/",
    )

    class FakeClient:
        def search(self, subreddits, queries, limit):
            return [submission]

    src = RedditSource(client=FakeClient(), subreddits=["x"], queries=["agent"])
    arts = src.fetch(datetime(2020, 1, 1, tzinfo=UTC))
    assert src.name == "reddit"
    assert len(arts) == 1
    a = arts[0]
    assert a.source_id == "abc"
    assert a.author == "redditor1"
    assert a.url.endswith("/r/x/comments/abc/")
