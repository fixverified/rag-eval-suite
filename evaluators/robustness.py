"""Robustness evaluators: do answers stay consistent? Descriptive, since no failure labels apply. Copy this file.

embed(texts) -> list of vectors
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

@dataclass(frozen=True)
class EvalResult:
    """Higher scores are always better. `passed` is None when no threshold is given."""

    name: str
    score: float
    threshold: float | None
    passed: bool | None
    details: dict[str, Any] = field(default_factory=dict)


def _result(name: str, score: float, threshold: float | None, **details: Any) -> EvalResult:
    return EvalResult(name, float(score), threshold, None if threshold is None else score >= threshold, details)


_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def number_consistency(answers: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Share of answer pairs stating the same numbers. Use on repeat runs or query paraphrases."""
    sets = [{m.replace(",", "").rstrip(".") for m in _NUMBER.findall(a)} for a in answers]
    pairs = list(combinations(sets, 2))
    if not pairs:
        raise ValueError("needs at least two answers")
    return _result("number_consistency", sum(a == b for a, b in pairs) / len(pairs), threshold)


def semantic_consistency(answers: Sequence[str], embed: Callable[[Sequence[str]], Sequence[Sequence[float]]], threshold: float | None = None) -> EvalResult:
    """Mean cosine similarity across answer pairs."""
    vectors = embed(list(answers))
    pairs = list(combinations(vectors, 2))
    if not pairs:
        raise ValueError("needs at least two answers")
    cosine = lambda a, b: sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)
    return _result("semantic_consistency", sum(cosine(a, b) for a, b in pairs) / len(pairs), threshold)
