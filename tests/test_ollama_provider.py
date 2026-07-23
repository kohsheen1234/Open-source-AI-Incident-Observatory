import httpx

from agentwatch.classify.providers.ollama import OllamaProvider


def test_ollama_maps_chat_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": '{"relevance":"relevant"}'}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    p = OllamaProvider(model="test-model", client=client)
    res = p.generate("sys", "user")
    assert res.text == '{"relevance":"relevant"}'
    assert res.model_name == "test-model"
    assert p.name == "test-model"
