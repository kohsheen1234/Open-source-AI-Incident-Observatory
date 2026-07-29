import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from agentwatch.collectors.base import RawArtifact


@runtime_checkable
class StorageBackend(Protocol):
    """Where raw evidence is persisted. Swap the implementation without touching the
    pipeline: LocalArtifactStore today; an S3ArtifactStore is the natural next step."""

    def store(self, artifact: RawArtifact) -> Path | None: ...


class LocalArtifactStore:
    """Content-addressed evidence on the local filesystem."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)

    def _dir_for(self, artifact: RawArtifact) -> Path:
        if artifact.published_at is not None:
            year = f"{artifact.published_at.year:04d}"
            month = f"{artifact.published_at.month:02d}"
        else:
            year, month = "unknown", "unknown"
        return self.base_dir / artifact.source / year / month

    def store(self, artifact: RawArtifact) -> Path | None:
        target_dir = self._dir_for(artifact)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{artifact.content_hash}.json"
        if not path.exists():
            path.write_text(json.dumps(artifact.raw, sort_keys=True, indent=2, default=str))
        return path


class NullArtifactStore:
    """Discards evidence — used by benchmarks to isolate DB-ingestion throughput."""

    def store(self, artifact: RawArtifact) -> Path | None:  # noqa: ARG002
        return None


# Backwards-compatible default name (local filesystem store).
ArtifactStore = LocalArtifactStore
