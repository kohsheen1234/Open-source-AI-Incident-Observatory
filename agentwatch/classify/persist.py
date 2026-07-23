from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentwatch.classify.classifier import classify_text
from agentwatch.classify.provider import LLMProvider
from agentwatch.db.models import Classification, Incident


def classify_pending(session: Session, provider: LLMProvider, *, limit: int | None = None) -> int:
    classified_ids = select(Classification.incident_id)
    stmt = select(Incident).where(Incident.id.notin_(classified_ids))
    if limit is not None:
        stmt = stmt.limit(limit)
    incidents = session.scalars(stmt).all()
    count = 0
    for incident in incidents:
        outcome = classify_text(f"{incident.title}\n{incident.body}", provider)
        r = outcome.result
        session.add(
            Classification(
                incident_id=incident.id,
                model_name=outcome.model_name,
                prompt_version=outcome.prompt_version,
                relevance=r.relevance.value,
                incident_type=r.incident_type.value,
                severity=r.severity,
                evidence_quality=r.evidence_quality.value if r.evidence_quality else None,
                autonomy_level=r.autonomy_level.value if r.autonomy_level else None,
                confidence=r.confidence,
                abstained=r.abstained,
                reasoning_summary=r.reasoning_summary,
                cost_usd=outcome.cost_usd,
                latency_ms=outcome.latency_ms,
                created_at=datetime.now(UTC),
            )
        )
        count += 1
    return count
