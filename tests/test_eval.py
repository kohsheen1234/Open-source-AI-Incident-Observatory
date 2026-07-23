from agentwatch.classify.providers.baseline import BaselineProvider
from agentwatch.eval.runner import load_dataset, run_eval

REGRESSION_FLOOR = 0.6


def test_dataset_loads():
    data = load_dataset()
    assert len(data) >= 16
    assert all("text" in row and "incident_type" in row for row in data)


def test_baseline_meets_regression_floor():
    report = run_eval(BaselineProvider())
    assert report.n >= 16
    assert report.metrics.macro_f1 >= REGRESSION_FLOOR, (
        f"macro-F1 {report.metrics.macro_f1:.3f} fell below floor {REGRESSION_FLOOR}"
    )
    assert 0.0 <= report.abstention_rate <= 1.0
