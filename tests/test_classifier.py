from agentwatch.classify.classifier import classify_text
from agentwatch.classify.provider import LLMResult
from agentwatch.classify.providers.baseline import BaselineProvider


class BadProvider:
    name = "bad"

    def generate(self, system, user):
        return LLMResult(text="not json at all", model_name="bad")


def test_classifier_happy_path_uses_baseline():
    out = classify_text("the agent deleted my repo with rm -rf", BaselineProvider())
    assert out.result.incident_type.value == "destructive_action"
    assert out.result.abstained is False
    assert out.model_name == "baseline"
    assert out.prompt_version


def test_classifier_abstains_on_malformed_output():
    out = classify_text("anything", BadProvider())
    assert out.result.abstained is True
    assert out.result.relevance.value == "insufficient_evidence"


def test_insufficient_evidence_marks_abstained():
    out = classify_text("not sure what happened here", BaselineProvider())
    assert out.result.relevance.value == "insufficient_evidence"
    assert out.result.abstained is True
