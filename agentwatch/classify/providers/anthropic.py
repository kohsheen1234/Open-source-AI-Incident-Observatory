import time

from agentwatch.classify.provider import LLMResult

# Illustrative per-token prices (USD); adjust to the model actually used.
_INPUT_PER_TOKEN = 3.0 / 1_000_000
_OUTPUT_PER_TOKEN = 15.0 / 1_000_000


class AnthropicProvider:
    def __init__(self, client, model: str = "claude-sonnet-5", max_tokens: int = 512) -> None:
        self._client = client
        self.model = model
        self.name = model
        self.max_tokens = max_tokens

    def generate(self, system: str, user: str) -> LLMResult:
        started = time.perf_counter()
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        text = msg.content[0].text
        cost = (
            msg.usage.input_tokens * _INPUT_PER_TOKEN + msg.usage.output_tokens * _OUTPUT_PER_TOKEN
        )
        return LLMResult(text=text, model_name=self.model, cost_usd=cost, latency_ms=latency_ms)
