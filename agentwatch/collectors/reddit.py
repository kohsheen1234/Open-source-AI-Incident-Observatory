from datetime import UTC, datetime
from typing import Protocol

from agentwatch.collectors.base import RawArtifact
from agentwatch.config import get_settings


def reddit_enabled() -> bool:
    s = get_settings()
    return bool(s.reddit_client_id and s.reddit_client_secret)


class RedditClient(Protocol):
    def search(self, subreddits: list[str], queries: list[str], limit: int) -> list: ...


class RedditSource:
    name = "reddit"

    def __init__(self, client: RedditClient, subreddits: list[str], queries: list[str]) -> None:
        self._client = client
        self.subreddits = subreddits
        self.queries = queries

    def fetch(self, since: datetime) -> list[RawArtifact]:
        since_ts = since.timestamp()
        artifacts: list[RawArtifact] = []
        for sub in self._client.search(self.subreddits, self.queries, limit=100):
            if getattr(sub, "created_utc", 0) < since_ts:
                continue
            author = getattr(sub, "author", None)
            artifacts.append(
                RawArtifact(
                    source=self.name,
                    source_id=str(sub.id),
                    url=f"https://www.reddit.com{sub.permalink}",
                    title=sub.title or "",
                    body=getattr(sub, "selftext", "") or "",
                    author=getattr(author, "name", None) if author else None,
                    published_at=datetime.fromtimestamp(sub.created_utc, tz=UTC),
                    raw={"id": sub.id, "title": sub.title, "permalink": sub.permalink},
                )
            )
        return artifacts
