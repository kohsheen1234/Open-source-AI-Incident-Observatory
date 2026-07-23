from datetime import UTC, datetime

import httpx

from agentwatch.collectors.base import RawArtifact
from agentwatch.collectors.http import get_json

API = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsSource:
    name = "hackernews"

    def __init__(self, queries: list[str], client: httpx.Client | None = None) -> None:
        self.queries = queries
        self._client = client

    def fetch(self, since: datetime) -> list[RawArtifact]:
        since_ts = int(since.timestamp())
        artifacts: list[RawArtifact] = []
        seen: set[str] = set()
        for query in self.queries:
            data = get_json(
                API,
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{since_ts}",
                },
                client=self._client,
            )
            for hit in data.get("hits", []):
                object_id = str(hit.get("objectID", ""))
                if not object_id or object_id in seen:
                    continue
                seen.add(object_id)
                artifacts.append(self._to_artifact(hit))
        return artifacts

    def _to_artifact(self, hit: dict) -> RawArtifact:
        created = hit.get("created_at_i")
        published = datetime.fromtimestamp(created, tz=UTC) if created else None
        return RawArtifact(
            source=self.name,
            source_id=str(hit.get("objectID", "")),
            url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            title=hit.get("title") or hit.get("story_title") or "",
            body=hit.get("story_text") or hit.get("comment_text") or "",
            author=hit.get("author"),
            published_at=published,
            raw=hit,
        )
