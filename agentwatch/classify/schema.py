from pydantic import BaseModel, Field, field_validator

from agentwatch.classify.taxonomy import (
    AutonomyLevel,
    EvidenceQuality,
    IncidentType,
    Relevance,
)


class ClassificationResult(BaseModel):
    relevance: Relevance
    incident_type: IncidentType = IncidentType.INSUFFICIENT_EVIDENCE
    severity: int | None = None
    evidence_quality: EvidenceQuality | None = None
    autonomy_level: AutonomyLevel | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str = ""
    abstained: bool = False

    @field_validator("incident_type", mode="before")
    @classmethod
    def _null_incident_type_is_insufficient(cls, v: object) -> object:
        # A model that judges a report `not_relevant` legitimately returns a null
        # incident_type — there is no incident to type. Treat null/absent as
        # `insufficient_evidence` rather than rejecting the whole (otherwise valid)
        # classification and losing its relevance verdict and confidence.
        if v is None:
            return IncidentType.INSUFFICIENT_EVIDENCE
        return v

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
