from pydantic import BaseModel, Field

from agentwatch.classify.taxonomy import (
    AutonomyLevel,
    EvidenceQuality,
    IncidentType,
    Relevance,
)


class ClassificationResult(BaseModel):
    relevance: Relevance
    incident_type: IncidentType
    severity: int | None = None
    evidence_quality: EvidenceQuality | None = None
    autonomy_level: AutonomyLevel | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str = ""
    abstained: bool = False

    @classmethod
    def abstain(cls, reason: str) -> "ClassificationResult":
        return cls(
            relevance=Relevance.INSUFFICIENT_EVIDENCE,
            incident_type=IncidentType.INSUFFICIENT_EVIDENCE,
            severity=None,
            evidence_quality=None,
            autonomy_level=AutonomyLevel.UNKNOWN,
            confidence=0.0,
            reasoning_summary=reason,
            abstained=True,
        )
