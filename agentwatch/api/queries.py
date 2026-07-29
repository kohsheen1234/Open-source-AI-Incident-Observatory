import csv
import io
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentwatch.db.models import Classification, Incident, RawArtifact, Review


def _latest_class_subq():
    return (
        select(
            Classification.incident_id.label("incident_id"),
            func.max(Classification.id).label("cid"),
        )
        .group_by(Classification.incident_id)
        .subquery()
    )


def _filtered_select(source, incident_type, abstained, min_severity, relevance):
    sub = _latest_class_subq()
    stmt = (
        select(Incident, Classification, RawArtifact.source_id)
        .join(RawArtifact, RawArtifact.id == Incident.raw_artifact_id)
        .outerjoin(sub, sub.c.incident_id == Incident.id)
        .outerjoin(Classification, Classification.id == sub.c.cid)
    )
    conds = []
    if source is not None:
        conds.append(Incident.source == source)
    if incident_type is not None:
        conds.append(Classification.incident_type == incident_type)
    if relevance is not None:
        conds.append(Classification.relevance == relevance)
    if abstained is not None:
        conds.append(Classification.abstained == abstained)
    if min_severity is not None:
        conds.append(Classification.severity >= min_severity)
    if conds:
        stmt = stmt.where(*conds)
    return stmt


def list_incidents(
    session: Session,
    *,
    source=None,
    incident_type=None,
    abstained=None,
    min_severity=None,
    relevance=None,
    limit=50,
    offset=0,
):
    stmt = _filtered_select(source, incident_type, abstained, min_severity, relevance)
    total = session.scalar(select(func.count()).select_from(stmt.subquery()))
    page = stmt.order_by(Incident.id.desc()).limit(limit).offset(offset)
    rows = [(inc, cls, sid) for inc, cls, sid in session.execute(page).all()]
    return rows, int(total or 0)


def get_incident(session: Session, incident_id: int):
    inc = session.get(Incident, incident_id)
    if inc is None:
        return None
    source_id = session.scalar(
        select(RawArtifact.source_id).where(RawArtifact.id == inc.raw_artifact_id)
    )
    classes = session.scalars(
        select(Classification).where(Classification.incident_id == incident_id)
    ).all()
    class_ids = [c.id for c in classes]
    reviews = (
        session.scalars(select(Review).where(Review.classification_id.in_(class_ids))).all()
        if class_ids
        else []
    )
    return inc, source_id, list(classes), list(reviews)


def add_review(session: Session, incident_id: int, *, reviewer: str, decision: str, notes):
    latest = session.scalar(
        select(Classification)
        .where(Classification.incident_id == incident_id)
        .order_by(Classification.id.desc())
        .limit(1)
    )
    if latest is None:
        raise ValueError(f"incident {incident_id} has no classification to review")
    review = Review(
        classification_id=latest.id,
        reviewer=reviewer,
        decision=decision,
        notes=notes,
        reviewed_at=datetime.now(UTC),
    )
    session.add(review)
    session.flush()
    return review


def stats(session: Session) -> dict:
    total_incidents = session.scalar(select(func.count()).select_from(Incident)) or 0
    # Latest classification per incident, so counts reflect the current label (not history).
    sub = _latest_class_subq()
    rows = session.execute(
        select(Classification.incident_type, Classification.abstained, Classification.relevance)
        .join(sub, Classification.id == sub.c.cid)
    ).all()
    by_type: dict[str, int] = {}
    by_relevance: dict[str, int] = {}
    abstained = confirmed = 0
    for incident_type, is_abstained, relevance in rows:
        abstained += 1 if is_abstained else 0
        by_relevance[relevance] = by_relevance.get(relevance, 0) + 1
        if relevance == "relevant":
            confirmed += 1
            # Only break down real incidents by type; non-incidents would swamp it.
            by_type[incident_type] = by_type.get(incident_type, 0) + 1
    total_classified = len(rows)
    return {
        "total_incidents": int(total_incidents),
        "total_classified": total_classified,
        "confirmed_incidents": confirmed,
        "abstention_rate": (abstained / total_classified) if total_classified else 0.0,
        "by_incident_type": by_type,
        "by_relevance": by_relevance,
    }


def incidents_csv(session: Session) -> str:
    rows, _ = list_incidents(session, limit=100_000, offset=0)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "source", "url", "title", "published_at", "incident_type", "severity", "confidence"]
    )
    for inc, cls, _sid in rows:
        writer.writerow(
            [
                inc.id,
                inc.source,
                inc.url,
                inc.title,
                inc.published_at.isoformat() if inc.published_at else "",
                cls.incident_type if cls else "",
                cls.severity if cls else "",
                cls.confidence if cls else "",
            ]
        )
    return buffer.getvalue()
