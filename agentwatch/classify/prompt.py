from agentwatch.classify.taxonomy import (
    AutonomyLevel,
    EvidenceQuality,
    IncidentType,
    Relevance,
)

PROMPT_VERSION = "v1"

_TYPES = ", ".join(t.value for t in IncidentType)
_REL = ", ".join(r.value for r in Relevance)
_EVID = ", ".join(e.value for e in EvidenceQuality)
_AUTO = ", ".join(a.value for a in AutonomyLevel)

SYSTEM = f"""You are an analyst classifying public reports of AI-agent incidents.
Given a report, respond with a single JSON object and nothing else.

Fields:
- relevance: one of [{_REL}]
- incident_type: one of [{_TYPES}]
- severity: integer 1-5, or null
- evidence_quality: one of [{_EVID}], or null
- autonomy_level: one of [{_AUTO}]
- confidence: number between 0 and 1
- reasoning_summary: one short sentence

Rules:
- If the report does not describe an AI-agent incident, use relevance "not_relevant".
- If there is not enough information to decide, use relevance "insufficient_evidence"
  and incident_type "insufficient_evidence". Do not guess.
Respond with JSON only."""


def build_prompt(text: str) -> tuple[str, str]:
    return SYSTEM, f"Report:\n{text}\n\nClassify it as JSON."
