import pytest

from rag_eval_suite.stats import achieved_fpr, auprc, auroc, cluster_rate, components, holm, paired_difference, question_rate, threshold_for_fpr, wilson


def test_wilson_matches_protocol_example():
    low, high = wilson(16, 20)
    assert (round(low, 2), round(high, 2)) == (0.58, 0.92)
    assert wilson(0, 30)[1] == pytest.approx(0.1135, abs=0.001)


def test_threshold_respects_target():
    clean = [0.1] + [0.5] * 19 + [0.9] * 80
    threshold = threshold_for_fpr(clean, target=0.05)
    assert threshold == 0.5
    assert achieved_fpr(clean, threshold) == 0.01


def test_binary_scores_report_real_rate():
    clean = [0.0] * 10 + [1.0] * 90
    threshold = threshold_for_fpr(clean, target=0.05)
    assert threshold == 0.0
    assert achieved_fpr(clean, threshold) == 0


def test_question_rate_weights_questions_equally():
    rates = question_rate([("a", True), ("a", False), ("b", True)])
    assert rates == {"a": 0.5, "b": 1.0}


def test_components_group_shared_pages():
    groups = components({"a": [("501", 1)], "b": [("501", 1), ("501", 2)], "c": [("501", 2)], "d": [("969", 5)]})
    assert groups["a"] == groups["b"] == groups["c"]
    assert groups["d"] != groups["a"]


def test_cluster_interval_widens_when_questions_are_correlated():
    values = {f"q{i}": float(i < 50) for i in range(100)}
    independent = cluster_rate(values, {q: q for q in values})
    clustered = cluster_rate(values, {q: "x" if v else "y" for q, v in values.items()})
    assert independent.value == clustered.value == 0.5
    assert clustered.high - clustered.low > independent.high - independent.low
    assert (clustered.questions, clustered.components) == (100, 2)


def test_empty_rate_is_nan_rather_than_zero():
    assert cluster_rate({}, {}).questions == 0


def test_paired_difference_detects_real_gap_and_not_noise():
    component_of = {f"q{i}": f"q{i}" for i in range(60)}
    better = {q: 1.0 for q in component_of}
    worse = {q: 0.0 for q in component_of}
    assert paired_difference(better, worse, component_of)[3] == 0
    mixed = {q: float(i % 2) for i, q in enumerate(component_of)}
    assert paired_difference(mixed, {q: 0.5 for q in mixed}, component_of)[3] > 0.5


def test_holm_is_monotonic():
    adjusted = holm({"a": 0.01, "b": 0.02, "c": 0.5})
    assert adjusted == {"a": 0.03, "b": 0.04, "c": 0.5}


def test_auroc_counts_ties_as_half():
    assert auroc([0.1, 0.2], [0.8, 0.9]) == 1
    assert auroc([0.5], [0.5]) == 0.5


def test_auprc_is_one_when_bad_scores_are_lowest():
    assert auprc([0.1, 0.2], [0.8, 0.9]) == 1
    assert auprc([0.9], [0.1, 0.2, 0.3]) == pytest.approx(0.25)
