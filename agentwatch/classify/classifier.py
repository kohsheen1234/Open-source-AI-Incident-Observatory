import json
from dataclasses import dataclass

from pydantic import ValidationError

from agentwatch.classify.prompt import PROMPT_VERSION, build_prompt
from agentwatch.classify.provider import LLMProvider
from agentwatch.classify.schema import ClassificationResult
from agentwatch.classify.taxonomy import Relevance
from agentwatch.logging import get_logger

log = get_logger("classifier")


@dataclass
class ClassifyOutcome:
    result: ClassificationResult
    model_name: str
    prompt_version: str
    cost_usd: float
    latency_ms: int


def _parse(text: str) -> ClassificationResult:
    return ClassificationResult.model_validate_json(text)


def classify_text(text: str, provider: LLMProvider) -> ClassifyOutcome:
    system, user = build_prompt(text)
    cost = 0.0
    latency = 0
    result: ClassificationResult | None = None
    for attempt in range(2):  # one retry on malformed output
        llm = provider.generate(system, user)
        cost += llm.cost_usd
        latency += llm.latency_ms
        try:
            result = _parse(llm.text)
            break
        except (ValidationError, json.JSONDecodeError):
            log.warning("classify.parse_failed", attempt=attempt, model=llm.model_name)
    if result is None:
        result = ClassificationResult.abstain("model returned unparseable output")
    if result.relevance is Relevance.INSUFFICIENT_EVIDENCE:
        result.abstained = True
    return ClassifyOutcome(
        result=result,
        model_name=provider.name,
        prompt_version=PROMPT_VERSION,
        cost_usd=cost,
        latency_ms=latency,
    )
