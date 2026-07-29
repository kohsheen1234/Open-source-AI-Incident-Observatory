import json

from agentwatch.classify.provider import LLMResult


class MajorityProvider:
    """Constant-class sanity floor.

    Always predicts the most frequent label in the labelled set (``relevant`` /
    ``destructive_action``) and never abstains. It carries zero information about the
    input — its only job is to set the floor that a *useful* classifier must clear. A
    system that cannot beat the majority baseline has learned nothing.
    """

    name = "majority"

    def generate(self, system: str, user: str) -> LLMResult:  # noqa: ARG002
        payload = {
            "relevance": "relevant",
            "incident_type": "destructive_action",
            "severity": 3,
            "evidence_quality": "speculation",
            "autonomy_level": "unknown",
            "confidence": 0.5,
            "reasoning_summary": "majority-class baseline (no input signal used)",
        }
        return LLMResult(text=json.dumps(payload), model_name="majority")
