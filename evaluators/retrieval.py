"""Retrieval evaluators. Copy this file into your project. Standard library only.

Rank metrics need labeled relevant ids and are undefined when a question has none. They raise ValueError in that case,
so an unanswerable question can't look like a pass or a miss.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
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


def _check(retrieved: Sequence[str], relevant: Sequence[str], k: int | None) -> tuple[list[str], set[str]]:
    if not relevant:
        raise ValueError("rank metrics are undefined without relevant ids")
    return list(retrieved if k is None else retrieved[:k]), set(relevant)


def recall_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int, threshold: float | None = None) -> EvalResult:
    """Share of relevant ids found in the top k."""
    top, gold = _check(retrieved, relevant, k)
    return _result("recall_at_k", len(gold & set(top)) / len(gold), threshold, k=k)


def precision_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int, threshold: float | None = None) -> EvalResult:
    """Share of the top k that is relevant, dividing by k even if fewer were returned."""
    top, gold = _check(retrieved, relevant, k)
    return _result("precision_at_k", sum(item in gold for item in top) / k, threshold, k=k)


def hit_rate(retrieved: Sequence[str], relevant: Sequence[str], k: int, threshold: float | None = None) -> EvalResult:
    """1 if anything relevant appears in the top k, otherwise 0."""
    top, gold = _check(retrieved, relevant, k)
    return _result("hit_rate", float(bool(gold & set(top))), threshold, k=k)


def mrr(retrieved: Sequence[str], relevant: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Reciprocal rank of the first relevant id."""
    top, gold = _check(retrieved, relevant, None)
    rank = next((i for i, item in enumerate(top, 1) if item in gold), None)
    return _result("mrr", 1 / rank if rank else 0.0, threshold, first_rank=rank)


def average_precision(retrieved: Sequence[str], relevant: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Average precision. Averaging it across queries gives MAP."""
    top, gold = _check(retrieved, relevant, None)
    hits, total, seen = 0, 0.0, set()
    for rank, item in enumerate(top, 1):
        if item in gold and item not in seen:
            seen.add(item)
            hits += 1
            total += hits / rank
    return _result("average_precision", total / len(gold), threshold)


def ndcg_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int, threshold: float | None = None) -> EvalResult:
    """Binary nDCG in the top k."""
    top, gold = _check(retrieved, relevant, k)
    dcg = sum(1 / math.log2(rank + 1) for rank, item in enumerate(top, 1) if item in gold)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(gold)) + 1))
    return _result("ndcg_at_k", dcg / ideal, threshold, k=k)


def _normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", re.sub(r"-\s*", "", text)).strip()


def evidence_coverage(quotes: Sequence[str], contexts: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Share of gold evidence quotes appearing word for word in a retrieved passage. Needs no ids, so it survives re-chunking."""
    if not quotes:
        raise ValueError("evidence coverage is undefined without quotes")
    found = [any(_normalize(quote) in _normalize(context) for context in contexts) for quote in quotes]
    return _result("evidence_coverage", sum(found) / len(found), threshold, missing=[q for q, ok in zip(quotes, found) if not ok])


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def query_term_overlap(query: str, contexts: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Descriptive: mean share of query terms present per passage."""
    terms = _tokens(query)
    if not terms or not contexts:
        return _result("query_term_overlap", 0.0, threshold)
    return _result("query_term_overlap", sum(len(terms & _tokens(c)) / len(terms) for c in contexts) / len(contexts), threshold)


def duplicate_free_rate(contexts: Sequence[str], similarity: float = 0.8, threshold: float | None = None) -> EvalResult:
    """Descriptive: share of passages that aren't near-duplicates of an earlier passage, by token Jaccard."""
    kept: list[set[str]] = []
    for context in contexts:
        tokens = _tokens(context)
        if not any(len(tokens & other) / max(len(tokens | other), 1) >= similarity for other in kept):
            kept.append(tokens)
    return _result("duplicate_free_rate", len(kept) / max(len(contexts), 1), threshold)


def source_diversity(sources: Sequence[str], threshold: float | None = None) -> EvalResult:
    """Descriptive: distinct sources divided by passages."""
    return _result("source_diversity", len(set(sources)) / max(len(sources), 1), threshold)
