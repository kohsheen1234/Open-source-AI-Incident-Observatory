import json
from dataclasses import dataclass
from importlib.resources import files

from agentwatch.classify.classifier import classify_text
from agentwatch.classify.provider import LLMProvider
from agentwatch.eval.metrics import Metrics, compute_metrics

DATASET = files("agentwatch.eval") / "dataset.json"


@dataclass
class EvalReport:
    metrics: Metrics
    abstention_rate: float
    total_cost_usd: float
    avg_latency_ms: float
    n: int


def load_dataset(path=None) -> list[dict]:
    source = path if path is not None else DATASET
    if hasattr(source, "read_text"):
        return json.loads(source.read_text())
    with open(source) as fh:
        return json.load(fh)


def run_eval(provider: LLMProvider, dataset: list[dict] | None = None) -> EvalReport:
    rows = dataset if dataset is not None else load_dataset()
    pairs: list[tuple[str, str]] = []
    abstained = 0
    total_cost = 0.0
    total_latency = 0
    for row in rows:
        outcome = classify_text(row["text"], provider)
        pairs.append((row["incident_type"], outcome.result.incident_type.value))
        abstained += 1 if outcome.result.abstained else 0
        total_cost += outcome.cost_usd
        total_latency += outcome.latency_ms
    n = len(rows)
    return EvalReport(
        metrics=compute_metrics(pairs),
        abstention_rate=abstained / n if n else 0.0,
        total_cost_usd=total_cost,
        avg_latency_ms=total_latency / n if n else 0.0,
        n=n,
    )
