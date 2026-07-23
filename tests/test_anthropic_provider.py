from types import SimpleNamespace

from agentwatch.classify.providers.anthropic import AnthropicProvider


class FakeMessages:
    def create(self, **kwargs):
        return SimpleNamespace(
            content=[SimpleNamespace(text='{"relevance":"relevant"}')],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
        )


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def test_anthropic_maps_response_and_costs():
    p = AnthropicProvider(client=FakeClient(), model="claude-x")
    res = p.generate("sys", "user")
    assert res.text == '{"relevance":"relevant"}'
    assert res.model_name == "claude-x"
    assert res.cost_usd > 0
