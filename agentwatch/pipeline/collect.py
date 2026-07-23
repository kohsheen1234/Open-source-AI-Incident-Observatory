from datetime import UTC, datetime

from agentwatch.collectors.base import DataSource
from agentwatch.db.models import CollectionRun
from agentwatch.db.session import session_scope
from agentwatch.logging import get_logger
from agentwatch.pipeline.ingest import persist_artifacts
from agentwatch.storage.artifacts import ArtifactStore

log = get_logger("collect")


def run_collection(source: DataSource, since: datetime, *, store: ArtifactStore) -> int:
    with session_scope() as s:
        run = CollectionRun(source=source.name, started_at=datetime.now(UTC), status="running")
        s.add(run)
        s.flush()
        run_id = run.id
        try:
            artifacts = source.fetch(since)
            result = persist_artifacts(s, artifacts, run_id=run_id, store=store)
            run.items_fetched = result.fetched
            run.items_new = result.new
            run.status = "success"
            log.info(
                "collection.success", source=source.name, fetched=result.fetched, new=result.new
            )
        except Exception as exc:  # isolate: record failure, do not propagate
            run.status = "failed"
            run.error = str(exc)
            log.error("collection.failed", source=source.name, error=str(exc))
        finally:
            run.finished_at = datetime.now(UTC)
        return run_id


def collect_all(sources: list[DataSource], since: datetime, *, store: ArtifactStore) -> list[int]:
    return [run_collection(src, since, store=store) for src in sources]
