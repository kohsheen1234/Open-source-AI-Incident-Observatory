import json
from pathlib import Path

from agentwatch.collectors.base import RawArtifact


class ArtifactStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)

    def _dir_for(self, artifact: RawArtifact) -> Path:
        if artifact.published_at is not None:
            year = f"{artifact.published_at.year:04d}"
            month = f"{artifact.published_at.month:02d}"
        else:
            year, month = "unknown", "unknown"
        return self.base_dir / artifact.source / year / month

    def store(self, artifact: RawArtifact) -> Path:
        target_dir = self._dir_for(artifact)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{artifact.content_hash}.json"
        if not path.exists():
            path.write_text(json.dumps(artifact.raw, sort_keys=True, indent=2, default=str))
        return path
