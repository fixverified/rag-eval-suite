"""Citation evaluators: do citations exist, support the claim, and cover the answer? Copy this file.

nli(premise, hypothesis) -> probability of entailment, from 0 to 1
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
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


_MARKER = re.compile(r"\[([^\[\]]+)\]")
_SENTENCE = re.compile(r"(?<=[.!?\]])\s+")


def extract_citations(answer: str) -> list[str]:
    """Pull ids from markers like [501-p7-c2]. Replace this if your format differs."""
    return _MARKER.findall(answer)


def citations_exist(cited: Sequence[str], valid_ids: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Share of cited ids that were really available. No citations scores 0."""
    if not cited:
        return _result("citations_exist", 0.0, threshold, reason="no citations")
    valid = set(valid_ids)
    return _result("citations_exist", sum(c in valid for c in cited) / len(cited), threshold, invalid=[c for c in cited if c not in valid])


def citation_support(answer: str, sources: Mapping[str, str], nli: Callable[[str, str], float], threshold: float | None = None) -> EvalResult:
    """The weakest cited sentence's entailment by the text it cites. A missing source counts as zero."""
    scores: list[float] = []
    for sentence in _SENTENCE.split(answer.strip()):
        ids = extract_citations(sentence)
        claim = _MARKER.sub("", sentence).strip()
        if ids and claim:
            scores.append(max(nli(sources[i], claim) if i in sources else 0.0 for i in ids))
    if not scores:
        return _result("citation_support", 0.0, threshold, reason="no cited sentences")
    return _result("citation_support", min(scores), threshold, cited_sentences=len(scores))


def citation_coverage(answer: str, threshold: float | None = None) -> EvalResult:
    """Share of sentences with at least one citation marker."""
    sentences = [s for s in _SENTENCE.split(answer.strip()) if s.strip()]
    return _result("citation_coverage", sum(bool(_MARKER.search(s)) for s in sentences) / max(len(sentences), 1), threshold)
