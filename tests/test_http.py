import httpx
import pytest

from agentwatch.collectors.http import get_json


def test_get_json_returns_parsed_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hits": [1, 2]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert get_json("https://x/api", client=client) == {"hits": [1, 2]}


def test_get_json_raises_on_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        get_json("https://x/api", client=client)
