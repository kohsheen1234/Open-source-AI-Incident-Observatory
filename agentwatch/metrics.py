from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentwatch.api.queries import stats
from agentwatch.db.models import CollectionRun


def render_metrics(session: Session) -> tuple[bytes, str]:
    registry = CollectorRegistry()
    st = stats(session)

    Gauge("agentwatch_incidents_total", "Total incidents", registry=registry).set(
        st["total_incidents"]
    )
    Gauge("agentwatch_classifications_total", "Total classifications", registry=registry).set(
        st["total_classified"]
    )
    Gauge("agentwatch_abstention_rate", "Abstention rate", registry=registry).set(
        st["abstention_rate"]
    )

    by_type = Gauge(
        "agentwatch_incidents_by_type",
        "Latest-classification incident counts by type",
        ["incident_type"],
        registry=registry,
    )
    for incident_type, count in st["by_incident_type"].items():
        by_type.labels(incident_type=incident_type).set(count)

    runs = Gauge(
        "agentwatch_collection_runs_total",
        "Collection runs by status",
        ["status"],
        registry=registry,
    )
    rows = session.execute(
        select(CollectionRun.status, func.count()).group_by(CollectionRun.status)
    ).all()
    for status_value, count in rows:
        runs.labels(status=status_value).set(count)

    return generate_latest(registry), CONTENT_TYPE_LATEST
