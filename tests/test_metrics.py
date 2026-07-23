from agentwatch.eval.metrics import compute_metrics


def test_perfect_predictions_give_macro_f1_one():
    pairs = [("a", "a"), ("b", "b"), ("a", "a")]
    m = compute_metrics(pairs)
    assert m.macro_f1 == 1.0
    assert m.support == {"a": 2, "b": 1}


def test_mixed_predictions():
    pairs = [("a", "a"), ("a", "b"), ("b", "b"), ("b", "b")]
    m = compute_metrics(pairs)
    assert m.recall["a"] == 0.5
    assert m.precision["a"] == 1.0
    assert 0.0 <= m.macro_f1 <= 1.0
    assert m.confusion["a"]["b"] == 1
