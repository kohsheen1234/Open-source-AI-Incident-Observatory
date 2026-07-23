from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from agentwatch.logging import get_logger

log = get_logger("http")


@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=8),
    reraise=True,
)
def get_json(url: str, params: dict | None = None, *, client: httpx.Client | None = None) -> Any:
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns_client:
            client.close()
