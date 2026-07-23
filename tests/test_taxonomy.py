from agentwatch.classify.schema import ClassificationResult
from agentwatch.classify.taxonomy import IncidentType, Relevance


def test_result_parses_from_dict():
    r = ClassificationResult.model_validate(
        {
            "relevance": "relevant",
            "incident_type": "destructive_action",
            "severity": 4,
            "evidence_quality": "first_party_claim",
            "autonomy_level": "tool_using_agent",
            "confidence": 0.8,
            "reasoning_summary": "ran rm",
        }
    )
    assert r.incident_type is IncidentType.DESTRUCTIVE_ACTION
    assert r.abstained is False


def test_abstain_helper():
    r = ClassificationResult.abstain("bad output")
    assert r.abstained is True
    assert r.relevance is Relevance.INSUFFICIENT_EVIDENCE
    assert r.incident_type is IncidentType.INSUFFICIENT_EVIDENCE
    assert r.confidence == 0.0
