import json

from agentwatch.classify.providers.baseline import BaselineProvider


def test_baseline_emits_parseable_labelled_json():
    p = BaselineProvider()
    res = p.generate("sys", "Report:\nthe agent deleted my repo with rm -rf\n")
    data = json.loads(res.text)
    assert data["incident_type"] == "destructive_action"
    assert data["relevance"] == "relevant"
    assert p.name == "baseline"
    assert res.cost_usd == 0.0


def test_baseline_abstains_on_thin_report():
    p = BaselineProvider()
    data = json.loads(p.generate("sys", "Report:\nnot sure what happened\n").text)
    assert data["relevance"] == "insufficient_evidence"
