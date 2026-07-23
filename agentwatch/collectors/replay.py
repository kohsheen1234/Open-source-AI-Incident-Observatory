import json
from datetime import datetime
from importlib.resources import files
from pathlib import Path

from agentwatch.collectors.base import RawArtifact

DEFAULT_FIXTURE = files("agentwatch.collectors.fixtures") / "incidents.json"


class ReplaySource:
    name = "replay"

    def __init__(self, path: Path | None = None) -> None:
        self._path = path

    def _load(self) -> list[dict]:
        if self._path is not None:
            return json.loads(Path(self._path).read_text())
        return json.loads(DEFAULT_FIXTURE.read_text())

    def fetch(self, since: datetime) -> list[RawArtifact]:
        artifacts: list[RawArtifact] = []
        for row in self._load():
            published = row.get("published_at")
            published_dt = datetime.fromisoformat(published) if published else None
            if published_dt is not None and published_dt < since:
                continue
            artifacts.append(
                RawArtifact(
                    source=self.name,
                    source_id=row["source_id"],
                    url=row["url"],
                    title=row["title"],
                    body=row["body"],
                    author=row.get("author"),
                    published_at=published_dt,
                    raw=row,
                )
            )
        return artifacts
