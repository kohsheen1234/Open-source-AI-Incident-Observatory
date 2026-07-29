import json
from collections import defaultdict
from dataclasses import dataclass, field
from importlib.resources import files

from agentwatch.classify.classifier import classify_text
from agentwatch.classify.provider import LLMProvider
from agentwatch.eval.metrics import Metrics, compute_metrics

DATASET = files("agentwatch.eval") / "dataset.json"


@dataclass
class FailureCase:
    """One misclassified example, kept for qualitative error analysis."""

    text: str
    gold_relevance: str
    gold_label: str
    pred_relevance: str
    pred_incident_type: str
    abstained: bool
    confidence: float


@dataclass
class EvalReport:
    n: int
    # Incident-type dimension: scored only on rows whose gold relevance is `relevant`
    # (the 9 concrete incident types). This is the discriminative task.
    incident_metrics: Metrics
    # Relevance dimension: the triage decision, scored on every row
    # (relevant / not_relevant / insufficient_evidence).
    relevance_metrics: Metrics
    # Selective prediction. A row is "fully correct" when the predicted relevance matches
    # gold and, for relevant rows, the incident type also matches.
    overall_accuracy: float  # fully-correct over ALL rows
    coverage: float  # fraction of rows the model did NOT abstain on
    selective_accuracy: float  # fully-correct over the ACCEPTED (non-abstained) rows
    # Abstention quality: when the model declines, is it right to?
    abstention_rate: float
    abstention_precision: float  # of abstentions, share that were genuinely under-evidenced
    abstention_recall: float  # of genuinely under-evidenced rows, share the model caught
    # Reliability table: (confidence_bin_low, empirical_accuracy, count).
    calibration: list[tuple[float, float, int]]
    total_cost_usd: float
    avg_latency_ms: float
    failures: list[FailureCase] = field(default_factory=list)


def load_dataset(path=None) -> list[dict]:
    source = path if path is not None else DATASET
    if hasattr(source, "read_text"):
        return json.loads(source.read_text())
    with open(source) as fh:
        return json.load(fh)


def _row_is_correct(gold_rel: str, gold_label: str, pred_rel: str, pred_it: str) -> bool:
    if pred_rel != gold_rel:
        return False
    if gold_rel == "relevant":
        return pred_it == gold_label
    return True


def run_eval(
    provider: LLMProvider,
    dataset: list[dict] | None = None,
    max_failures: int = 10,
) -> EvalReport:
    rows = dataset if dataset is not None else load_dataset()
    n = len(rows)

    incident_pairs: list[tuple[str, str]] = []  # (gold_label, pred) on relevant rows only
    relevance_pairs: list[tuple[str, str]] = []  # (gold_relevance, pred) on all rows

    abstained = abstain_correct = gold_insufficient = 0
    accepted = accepted_correct = overall_correct = 0
    total_cost = 0.0
    total_latency = 0
    calib: dict[int, list[int]] = defaultdict(lambda: [0, 0])  # bin -> [correct, count]
    failures: list[FailureCase] = []

    for row in rows:
        gold_rel = row["relevance"]
        gold_label = row["label"]
        outcome = classify_text(row["text"], provider)
        r = outcome.result
        pred_rel = r.relevance.value
        pred_it = r.incident_type.value
        total_cost += outcome.cost_usd
        total_latency += outcome.latency_ms

        relevance_pairs.append((gold_rel, pred_rel))
        if gold_rel == "relevant":
            incident_pairs.append((gold_label, pred_it))

        correct = _row_is_correct(gold_rel, gold_label, pred_rel, pred_it)
        overall_correct += correct

        if gold_rel == "insufficient_evidence":
            gold_insufficient += 1
        if r.abstained:
            abstained += 1
            if gold_rel == "insufficient_evidence":
                abstain_correct += 1
        else:
            accepted += 1
            accepted_correct += correct

        b = min(int(r.confidence * 10), 9)
        calib[b][0] += correct
        calib[b][1] += 1

        if not correct:
            failures.append(
                FailureCase(
                    text=row["text"],
                    gold_relevance=gold_rel,
                    gold_label=gold_label,
                    pred_relevance=pred_rel,
                    pred_incident_type=pred_it,
                    abstained=r.abstained,
                    confidence=r.confidence,
                )
            )

    # Surface the most instructive errors first: confident and wrong.
    failures.sort(key=lambda f: f.confidence, reverse=True)

    calibration = [
        (round(b / 10, 1), correct / count, count)
        for b, (correct, count) in sorted(calib.items())
        if count
    ]

    return EvalReport(
        n=n,
        incident_metrics=compute_metrics(incident_pairs),
        relevance_metrics=compute_metrics(relevance_pairs),
        overall_accuracy=overall_correct / n if n else 0.0,
        coverage=accepted / n if n else 0.0,
        selective_accuracy=accepted_correct / accepted if accepted else 0.0,
        abstention_rate=abstained / n if n else 0.0,
        abstention_precision=abstain_correct / abstained if abstained else 0.0,
        abstention_recall=abstain_correct / gold_insufficient if gold_insufficient else 0.0,
        calibration=calibration,
        total_cost_usd=total_cost,
        avg_latency_ms=total_latency / n if n else 0.0,
        failures=failures[:max_failures],
    )
