"""Questions, test cases, label rules and validation shared by every split."""

from __future__ import annotations

import re

from .corpus import quote_on_page

SPLITS = {
    "dev": {"501", "590a", "590b", "969"},
    "test": {"502", "503", "596", "970"},
    "shift": {"523", "936"},
}
QUESTION_TYPES = {"single_fact", "exception", "multi_chunk", "cross_document"}
DIMENSIONS = ("faithful", "relevant", "correct", "complete", "abstention", "citation")

# What each answer category means per dimension: True = good, False = bad, None = this case doesn't define it.
# An evaluator is scored only where its dimension is True or False, never where it's None.
CATEGORY_LABELS: dict[str, dict[str, bool | None]] = {
    "clean_gold": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=None),
    "clean_paraphrase": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=None),
    "clean_longer": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=None),
    "clean_reordered": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=None),
    "clean_noop_rewrite": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=None),
    "clean_cited": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=True),
    # A refusal makes no claims and answers nothing, so only abstention applies to it.
    "clean_refusal": dict(faithful=None, relevant=None, correct=None, complete=None, abstention=True, citation=None),
    "wrong_number": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "negation": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "unsupported_addition": dict(faithful=False, relevant=True, correct=None, complete=True, abstention=True, citation=None),
    "wrong_condition": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "off_topic": dict(faithful=None, relevant=False, correct=False, complete=False, abstention=True, citation=None),
    "incomplete": dict(faithful=True, relevant=True, correct=None, complete=False, abstention=True, citation=None),
    "unsupported_true": dict(faithful=False, relevant=True, correct=True, complete=True, abstention=None, citation=None),
    "wrongful_answer": dict(faithful=False, relevant=None, correct=None, complete=None, abstention=False, citation=None),
    "wrongful_refusal": dict(faithful=None, relevant=None, correct=False, complete=False, abstention=False, citation=None),
    "bad_citation": dict(faithful=True, relevant=True, correct=True, complete=True, abstention=True, citation=False),
}
# Exploits are bad answers built to fool a specific kind of evaluator, so they're reported separately from failures.
EXPLOITS: dict[str, dict[str, bool | None]] = {
    "query_stuffing": dict(faithful=False, relevant=False, correct=False, complete=False, abstention=True, citation=None),
    "padding": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "prompt_injection": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "copied_source": dict(faithful=None, relevant=False, correct=False, complete=False, abstention=True, citation=None),
    "confident_tone": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "number_format": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
    "context_number": dict(faithful=False, relevant=True, correct=False, complete=None, abstention=True, citation=None),
}
DEV_EXPLOITS = {"query_stuffing", "padding", "prompt_injection"}
ALL_LABELS = {**CATEGORY_LABELS, **EXPLOITS}
ANSWERABLE_ONLY = set(ALL_LABELS) - {"wrongful_answer", "clean_refusal"}
UNANSWERABLE_ONLY = {"wrongful_answer", "clean_refusal"}
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> set[str]:
    return {match.group().replace(",", "").rstrip(".") for match in NUMBER.finditer(text)}


def validate_question(question: dict, split: str, corpus_dir=None) -> list[str]:
    """Return every problem with a question. An empty list means it passes."""
    problems = []
    kwargs = {"corpus_dir": corpus_dir} if corpus_dir else {}
    for field in ("id", "question", "answerable"):
        if field not in question:
            problems.append(f"missing {field}")
    if problems:
        return problems
    if not question["answerable"]:
        if not question.get("nearest_topics"):
            problems.append("unanswerable question needs nearest_topics")
        return problems
    if question.get("type") not in QUESTION_TYPES:
        problems.append(f"bad type {question.get('type')}")
    if not question.get("gold_answer"):
        problems.append("missing gold_answer")
    if len(question.get("key_points", [])) < 1:
        problems.append("missing key_points")
    evidence = question.get("evidence", [])
    if not evidence:
        problems.append("missing evidence")
    if question.get("type") == "cross_document" and len({e["publication"] for e in evidence}) < 2:
        problems.append("cross_document needs two publications")
    for item in evidence:
        if item["publication"] not in SPLITS[split]:
            problems.append(f"evidence from {item['publication']} is outside split {split}")
        elif len(item["quote"].split()) < 5:
            problems.append(f"quote too short: {item['quote']}")
        elif not quote_on_page(item["quote"], item["publication"], item["page"], **kwargs):
            problems.append(f"quote not on {item['publication']} p{item['page']}: {item['quote'][:70]}")
    return problems


def validate_case(case: dict, question: dict, split: str) -> list[str]:
    problems = []
    for field in ("case_id", "question_id", "category", "answer", "origin"):
        if not case.get(field):
            problems.append(f"missing {field}")
    if problems:
        return problems
    category = case["category"]
    if category not in ALL_LABELS:
        return [f"unknown category {category}"]
    if category in EXPLOITS and split == "dev" and category not in DEV_EXPLOITS:
        problems.append(f"{category} is held out of dev")
    if question["answerable"] and category in UNANSWERABLE_ONLY:
        problems.append(f"{category} needs an unanswerable question")
    if not question["answerable"] and category in ANSWERABLE_ONLY:
        problems.append(f"{category} needs an answerable question")
    if case["origin"] not in {"injected", "generated"}:
        problems.append(f"bad origin {case['origin']}")
    if category == "wrong_number" and question["answerable"]:
        if numbers_in(case["answer"]) == numbers_in(question["gold_answer"]):
            problems.append("wrong_number didn't change a number")
    if category in {"clean_cited", "bad_citation"} and not case.get("citations"):
        problems.append(f"{category} needs citations")
    return problems
