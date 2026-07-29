"""Human-readable rendering of an :class:`EvalReport`.

Kept separate from the runner so the runner stays pure data — the same report can be
printed to a terminal, embedded in docs, or asserted on in tests.
"""

from agentwatch.eval.metrics import Metrics
from agentwatch.eval.runner import EvalReport


def _per_class_table(metrics: Metrics) -> list[str]:
    lines = [f"  {'class':<24} {'P':>6} {'R':>6} {'F1':>6} {'n':>5}"]
    for label in sorted(metrics.support, key=lambda k: -metrics.support[k]):
        if metrics.support[label] == 0:
            continue  # predicted-only class (e.g. abstain on a concrete-type dimension)
        lines.append(
            f"  {label:<24} {metrics.precision[label]:>6.2f} {metrics.recall[label]:>6.2f} "
            f"{metrics.f1[label]:>6.2f} {metrics.support[label]:>5}"
        )
    return lines


def format_report(provider_key: str, report: EvalReport) -> str:
    lines: list[str] = []
    lines.append(f"eval — provider={provider_key}  n={report.n}")
    lines.append("")
    lines.append("headline")
    lines.append(f"  incident-type macro-F1     {report.incident_metrics.macro_f1:.3f}")
    lines.append(f"  relevance macro-F1         {report.relevance_metrics.macro_f1:.3f}")
    lines.append(f"  overall accuracy           {report.overall_accuracy:.3f}")
    lines.append(
        f"  selective accuracy         {report.selective_accuracy:.3f} "
        f"(coverage {report.coverage:.3f})"
    )
    lines.append("")
    lines.append("abstention")
    lines.append(f"  rate                       {report.abstention_rate:.3f}")
    lines.append(f"  precision                  {report.abstention_precision:.3f}")
    lines.append(f"  recall                     {report.abstention_recall:.3f}")
    lines.append("")
    lines.append("cost / latency")
    lines.append(f"  total cost (usd)           {report.total_cost_usd:.4f}")
    lines.append(f"  avg latency (ms)           {report.avg_latency_ms:.1f}")
    lines.append("")
    lines.append("incident-type — per class (relevant rows only)")
    lines.extend(_per_class_table(report.incident_metrics))
    lines.append("")
    lines.append("relevance — per class (all rows)")
    lines.extend(_per_class_table(report.relevance_metrics))
    lines.append("")
    lines.append("calibration (confidence bin → empirical accuracy)")
    for low, acc, count in report.calibration:
        lines.append(f"  [{low:.1f}, {low + 0.1:.1f})   acc {acc:.2f}   n {count}")
    lines.append("")
    lines.append(f"failure cases (up to {len(report.failures)}, most confident first)")
    for i, f in enumerate(report.failures, 1):
        text = f.text if len(f.text) <= 88 else f.text[:85] + "..."
        gold = f.gold_label if f.gold_relevance == "relevant" else f.gold_relevance
        pred = (
            f.pred_incident_type if f.pred_relevance == "relevant" else f.pred_relevance
        )
        lines.append(f"  {i:>2}. conf={f.confidence:.2f}  gold={gold}  pred={pred}")
        lines.append(f"      {text}")
    return "\n".join(lines)
