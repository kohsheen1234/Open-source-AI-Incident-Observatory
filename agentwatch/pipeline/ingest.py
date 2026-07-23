from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentwatch.collectors.base import RawArtifact
from agentwatch.config import get_settings
from agentwatch.db.models import Incident
from agentwatch.db.models import RawArtifact as RawArtifactRow
from agentwatch.hashing import hash_author
from agentwatch.storage.artifacts import ArtifactStore


@dataclass
class IngestResult:
    fetched: int
    new: int


def persist_artifacts(
    session: Session,
    artifacts: list[RawArtifact],
    *,
    run_id: int | None,
    store: ArtifactStore,
) -> IngestResult:
    salt = get_settings().author_hash_salt
    new = 0
    for art in artifacts:
        digest = art.content_hash
        exists = session.scalar(
            select(RawArtifactRow.id).where(RawArtifactRow.content_hash == digest)
        )
        if exists:
            continue
        store.store(art)
        now = datetime.now(UTC)
        row = RawArtifactRow(
            source=art.source,
            source_id=art.source_id,
            url=art.url,
            content_hash=digest,
            raw_json=art.raw,
            fetched_at=now,
            collection_run_id=run_id,
        )
        session.add(row)
        session.flush()  # assign row.id
        session.add(
            Incident(
                raw_artifact_id=row.id,
                source=art.source,
                url=art.url,
                title=art.title,
                body=art.body,
                author_hash=hash_author(art.author, salt),
                published_at=art.published_at,
                ingested_at=now,
                content_hash=digest,
            )
        )
        new += 1
    return IngestResult(fetched=len(artifacts), new=new)
