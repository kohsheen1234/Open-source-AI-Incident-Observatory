from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from agentwatch.hashing import compute_content_hash


class RawArtifact(BaseModel):
    source: str
    source_id: str
    url: str
    title: str
    body: str
    author: str | None = None
    published_at: datetime | None = None
    raw: dict = Field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return compute_content_hash(
            {
                "source": self.source,
                "source_id": self.source_id,
                "url": self.url,
                "title": self.title,
                "body": self.body,
            }
        )


@runtime_checkable
class DataSource(Protocol):
    name: str

    def fetch(self, since: datetime) -> list[RawArtifact]: ...
