from agentwatch.classify.prompt import PROMPT_VERSION, build_prompt


def test_prompt_mentions_taxonomy_and_abstention():
    system, user = build_prompt("an agent deleted files")
    assert PROMPT_VERSION
    assert "insufficient_evidence" in system
    assert "JSON" in system
    assert "an agent deleted files" in user
