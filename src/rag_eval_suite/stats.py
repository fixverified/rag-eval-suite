"""Question-level recall and false positive rates, thresholds set on dev, and cluster bootstrap intervals."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

BOOTSTRAPS = 2000
SEED = 20261101
TARGET_FPR = 0.05


def wilson(successes: float, total: int, z: float = 1.959964) -> tuple[float, float]:
    if not total:
        return (0.0, 1.0)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def components(question_pages: dict[str, Iterable[tuple[str, int]]]) -> dict[str, str]:
    """Group questions that share an evidence page, using union-find. Returns question id -> component id."""
    parent = {q: q for q in question_pages}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    owner: dict[tuple[str, int], str] = {}
    for question, pages in question_pages.items():
        for page in pages:
            if page in owner:
                parent[find(question)] = find(owner[page])
            else:
                owner[page] = question
    return {q: find(q) for q in parent}


def threshold_for_fpr(clean_scores: Sequence[float], target: float = TARGET_FPR) -> float:
    """The highest threshold that fails at most `target` of clean controls. A score below the threshold is flagged.

    Discrete scores can't always hit the target, so report the achieved rate from achieved_fpr.
    """
    if not clean_scores:
        raise ValueError("no clean scores")
    ordered = sorted(set(clean_scores))
    chosen = ordered[0]
    for value in ordered:
        if sum(s < value for s in clean_scores) / len(clean_scores) <= target:
            chosen = value
        else:
            break
    return chosen


def achieved_fpr(clean_scores: Sequence[float], threshold: float) -> float:
    return sum(s < threshold for s in clean_scores) / len(clean_scores)


def question_rate(items: Iterable[tuple[str, bool]]) -> dict[str, float]:
    """Average repeated items within each question, so a question with more variants doesn't count for more."""
    grouped: dict[str, list[bool]] = defaultdict(list)
    for question, flagged in items:
        grouped[question].append(flagged)
    return {question: sum(flags) / len(flags) for question, flags in grouped.items()}


@dataclass(frozen=True)
class Rate:
    value: float
    low: float
    high: float
    questions: int
    components: int


def _percentile(sorted_values: Sequence[float], share: float) -> float:
    return sorted_values[min(int(share * len(sorted_values)), len(sorted_values) - 1)]


def cluster_rate(per_question: dict[str, float], component_of: dict[str, str], seed: int = SEED, draws: int = BOOTSTRAPS) -> Rate:
    """Mean over questions, with a 95% percentile bootstrap that resamples whole components."""
    if not per_question:
        return Rate(float("nan"), float("nan"), float("nan"), 0, 0)
    groups: dict[str, list[float]] = defaultdict(list)
    for question, value in per_question.items():
        groups[component_of[question]].append(value)
    names, rng, means = sorted(groups), random.Random(seed), []
    for _ in range(draws):
        total = count = 0.0
        for name in rng.choices(names, k=len(names)):
            total += sum(groups[name])
            count += len(groups[name])
        means.append(total / count)
    means.sort()
    value = sum(per_question.values()) / len(per_question)
    return Rate(value, _percentile(means, 0.025), _percentile(means, 0.975), len(per_question), len(names))


def paired_difference(a: dict[str, float], b: dict[str, float], component_of: dict[str, str], seed: int = SEED, draws: int = BOOTSTRAPS) -> tuple[float, float, float, float]:
    """Mean of a - b on shared questions: (difference, low, high, two-sided bootstrap p)."""
    shared = sorted(set(a) & set(b))
    groups: dict[str, list[float]] = defaultdict(list)
    for question in shared:
        groups[component_of[question]].append(a[question] - b[question])
    names, rng, means = sorted(groups), random.Random(seed), []
    for _ in range(draws):
        total = count = 0.0
        for name in rng.choices(names, k=len(names)):
            total += sum(groups[name])
            count += len(groups[name])
        means.append(total / count)
    means.sort()
    below = sum(m <= 0 for m in means) / draws
    above = sum(m >= 0 for m in means) / draws
    difference = sum(sum(g) for g in groups.values()) / max(len(shared), 1)
    return difference, _percentile(means, 0.025), _percentile(means, 0.975), min(1.0, 2 * min(below, above))


def holm(p_values: dict[str, float]) -> dict[str, float]:
    """Holm-adjusted p-values."""
    adjusted, largest = {}, 0.0
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    for index, (name, value) in enumerate(ordered):
        largest = max(largest, min(1.0, value * (len(ordered) - index)))
        adjusted[name] = largest
    return adjusted


def auroc(positive: Sequence[float], negative: Sequence[float]) -> float:
    """Chance a bad answer scores below a clean one, counting ties as half. Scores are higher-is-better."""
    if not positive or not negative:
        return float("nan")
    wins = sum((p < n) + 0.5 * (p == n) for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def auprc(positive: Sequence[float], negative: Sequence[float]) -> float:
    """Average precision for flagging bad answers, with tied scores handled as one group."""
    if not positive:
        return float("nan")
    tagged = [(s, True) for s in positive] + [(s, False) for s in negative]
    total, hits, seen, area = len(positive), 0, 0, 0.0
    for score in sorted({s for s, _ in tagged}):
        group = [bad for s, bad in tagged if s == score]
        new_hits = sum(group)
        hits += new_hits
        seen += len(group)
        area += new_hits / total * (hits / seen)
    return area


def threshold_stability(clean: dict[str, list[float]], component_of: dict[str, str], seed: int = SEED, draws: int = 500) -> tuple[float, float]:
    """The threshold's 2.5th and 97.5th percentiles when clean controls are resampled by component."""
    groups: dict[str, list[float]] = defaultdict(list)
    for question, scores in clean.items():
        groups[component_of[question]].extend(scores)
    names, rng, values = sorted(groups), random.Random(seed), []
    for _ in range(draws):
        sample = [s for name in rng.choices(names, k=len(names)) for s in groups[name]]
        values.append(threshold_for_fpr(sample))
    values.sort()
    return _percentile(values, 0.025), _percentile(values, 0.975)
