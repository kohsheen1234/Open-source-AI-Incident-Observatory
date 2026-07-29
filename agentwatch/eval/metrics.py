from dataclasses import dataclass


@dataclass
class Metrics:
    precision: dict[str, float]
    recall: dict[str, float]
    f1: dict[str, float]
    macro_f1: float
    confusion: dict[str, dict[str, int]]
    support: dict[str, int]


def compute_metrics(pairs: list[tuple[str, str]]) -> Metrics:
    labels = sorted({label for pair in pairs for label in pair})
    tp = dict.fromkeys(labels, 0)
    fp = dict.fromkeys(labels, 0)
    fn = dict.fromkeys(labels, 0)
    support = dict.fromkeys(labels, 0)
    confusion = {a: dict.fromkeys(labels, 0) for a in labels}

    for expected, predicted in pairs:
        support[expected] += 1
        confusion[expected][predicted] += 1
        if expected == predicted:
            tp[expected] += 1
        else:
            fp[predicted] += 1
            fn[expected] += 1

    precision, recall, f1 = {}, {}, {}
    for label in labels:
        p_den = tp[label] + fp[label]
        r_den = tp[label] + fn[label]
        precision[label] = tp[label] / p_den if p_den else 0.0
        recall[label] = tp[label] / r_den if r_den else 0.0
        f_den = precision[label] + recall[label]
        f1[label] = 2 * precision[label] * recall[label] / f_den if f_den else 0.0

    # Macro-average over classes that actually occur in the gold labels. A label that
    # appears only in predictions (e.g. the abstain class showing up on rows that have a
    # concrete gold type) would otherwise add a phantom zero and deflate the score.
    gold_labels = [label for label in labels if support[label] > 0]
    macro_f1 = sum(f1[label] for label in gold_labels) / len(gold_labels) if gold_labels else 0.0
    return Metrics(precision, recall, f1, macro_f1, confusion, support)
