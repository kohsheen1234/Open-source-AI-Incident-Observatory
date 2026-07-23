import time

import httpx

from agentwatch.classify.provider import LLMResult
from agentwatch.config import get_settings


class OllamaProvider:
    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.name = self.model
        self._client = client

    def generate(self, system: str, user: str) -> LLMResult:
        client = self._client or httpx.Client(timeout=120.0)
        owns = self._client is None
        started = time.perf_counter()
        try:
            resp = client.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "format": "json",
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
        finally:
            if owns:
                client.close()
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LLMResult(text=content, model_name=self.model, cost_usd=0.0, latency_ms=latency_ms)
