from agentwatch.classify.providers.baseline import BaselineProvider
from agentwatch.classify.providers.majority import MajorityProvider
from agentwatch.eval.runner import load_dataset, run_eval

# The keyword baseline runs against a deliberately hard set (misleading keywords in the
# hard negatives, incident reports phrased without their obvious trigger word). The floor
# is set below its measured score so a real regression trips it, not so it looks good.
INCIDENT_MACRO_F1_FLOOR = 0.20


def test_dataset_is_large_and_well_formed():
    data = load_dataset()
    assert len(data) >= 120
    assert all({"text", "label", "relevance"} <= row.keys() for row in data)
    relevances = {row["relevance"] for row in data}
    assert relevances == {"relevant", "not_relevant", "insufficient_evidence"}


def test_dataset_covers_full_taxonomy():
    from agentwatch.classify.taxonomy import IncidentType

    labels = {row["label"] for row in load_dataset() if row["relevance"] == "relevant"}
    concrete = {t.value for t in IncidentType if t.value != "insufficient_evidence"}
    missing = concrete - labels
    assert not missing, f"taxonomy classes with no relevant examples: {sorted(missing)}"


def test_baseline_meets_regression_floor():
    report = run_eval(BaselineProvider())
    assert report.n >= 120
    assert report.incident_metrics.macro_f1 >= INCIDENT_MACRO_F1_FLOOR, (
        f"incident macro-F1 {report.incident_metrics.macro_f1:.3f} "
        f"fell below floor {INCIDENT_MACRO_F1_FLOOR}"
    )
    assert 0.0 <= report.abstention_rate <= 1.0
    assert 0.0 <= report.selective_accuracy <= 1.0
    assert 0.0 <= report.coverage <= 1.0


def test_baseline_beats_majority():
    """The keyword baseline must carry real signal — it has to beat the constant-class
    floor on the discriminative (incident-type) task."""
    majority = run_eval(MajorityProvider())
    baseline = run_eval(BaselineProvider())
    assert baseline.incident_metrics.macro_f1 > majority.incident_metrics.macro_f1


def test_majority_never_abstains():
    report = run_eval(MajorityProvider())
    assert report.abstention_rate == 0.0
