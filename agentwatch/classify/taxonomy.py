from enum import Enum


class Relevance(str, Enum):
    RELEVANT = "relevant"
    NOT_RELEVANT = "not_relevant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class IncidentType(str, Enum):
    UNAUTHORIZED_ACTION = "unauthorized_action"
    RESISTANCE_TO_CORRECTION = "resistance_to_correction"
    DECEPTION = "deception"
    GOAL_PERSISTENCE = "goal_persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SANDBOX_ESCAPE = "sandbox_escape"
    DESTRUCTIVE_ACTION = "destructive_action"
    RESOURCE_ACQUISITION = "resource_acquisition"
    HARMLESS_MALFUNCTION = "harmless_malfunction"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceQuality(str, Enum):
    FIRST_PARTY_CLAIM = "first_party_claim"
    SECOND_HAND = "second_hand"
    SPECULATION = "speculation"


class AutonomyLevel(str, Enum):
    CHATBOT = "chatbot"
    TOOL_USING_AGENT = "tool_using_agent"
    AUTONOMOUS_AGENT = "autonomous_agent"
    UNKNOWN = "unknown"
