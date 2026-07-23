import json
import re

from agentwatch.classify.provider import LLMResult


def _matches(keyword: str, text: str) -> bool:
    # Prefix word-boundary match: "escalat" hits "escalated", but "lie" does not
    # hit "client" (no word boundary before the substring).
    return re.search(r"\b" + re.escape(keyword), text) is not None

# Ordered keyword rules → (incident_type, severity, autonomy_level).
_RULES: list[tuple[tuple[str, ...], str, int, str]] = [
    (
        ("rm -rf", "deleted", "delete", "wiped", "dropped the"),
        "destructive_action",
        4,
        "tool_using_agent",
    ),
    (
        ("sudo", "sudoers", "escalat", "root access", "permission"),
        "privilege_escalation",
        4,
        "autonomous_agent",
    ),
    (("sandbox", "escaped", "broke out"), "sandbox_escape", 5, "autonomous_agent"),
    (
        ("lied", "lie", "deceiv", "pretended", "never ran", "falsely"),
        "deception",
        3,
        "tool_using_agent",
    ),
    (
        ("kept", "again", "ignored", "refused to stop", "wouldn't stop"),
        "resistance_to_correction",
        3,
        "tool_using_agent",
    ),
    (
        ("without asking", "without confirm", "unauthor", "on its own"),
        "unauthorized_action",
        3,
        "tool_using_agent",
    ),
    (("harmless", "minor", "no harm", "typo"), "harmless_malfunction", 1, "chatbot"),
]


class BaselineProvider:
    """Deterministic, dependency-free classifier used as the default and in tests."""

    name = "baseline"

    def generate(self, system: str, user: str) -> LLMResult:
        text = user.lower()
        incident_type = None
        severity = None
        autonomy = "unknown"
        for keywords, itype, sev, auto in _RULES:
            if any(_matches(k, text) for k in keywords):
                incident_type, severity, autonomy = itype, sev, auto
                break

        if incident_type is None:
            payload = {
                "relevance": "insufficient_evidence",
                "incident_type": "insufficient_evidence",
                "severity": None,
                "evidence_quality": "speculation",
                "autonomy_level": "unknown",
                "confidence": 0.3,
                "reasoning_summary": "no clear incident signal",
            }
        else:
            relevance = "relevant" if incident_type != "harmless_malfunction" else "not_relevant"
            payload = {
                "relevance": relevance,
                "incident_type": incident_type,
                "severity": severity,
                "evidence_quality": "first_party_claim",
                "autonomy_level": autonomy,
                "confidence": 0.7,
                "reasoning_summary": f"matched {incident_type} keywords",
            }
        return LLMResult(text=json.dumps(payload), model_name="baseline")
