from datetime import UTC, datetime

import httpx

from agentwatch.collectors.hackernews import HackerNewsSource


def _client_returning(hits):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hits": hits})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_maps_hits_to_artifacts():
    hits = [
        {
            "objectID": "42",
            "title": "My agent deleted my repo",
            "story_text": "It ran rm without asking",
            "author": "bob",
            "created_at_i": 1_700_000_000,
            "url": None,
        }
    ]
    src = HackerNewsSource(queries=["agent"], client=_client_returning(hits))
    arts = src.fetch(since=datetime(2020, 1, 1, tzinfo=UTC))
    assert src.name == "hackernews"
    assert len(arts) == 1
    a = arts[0]
    assert a.source == "hackernews"
    assert a.source_id == "42"
    assert "deleted" in a.title
    assert a.author == "bob"
    assert a.url.endswith("item?id=42")
