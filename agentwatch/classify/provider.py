from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    model_name: str
    cost_usd: float = 0.0
    latency_ms: int = 0


class LLMProvider(Protocol):
    name: str

    def generate(self, system: str, user: str) -> LLMResult: ...
