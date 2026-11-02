"""Build each case's context, then run evaluators with their label dimension, keeping errors separate from scores."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from evaluators import abstention, citations, completeness, context, correctness, faithfulness, relevance

from . import models
from .corpus import load_pages, normalize
from .pipeline import TOP_K, Retriever

NO_GOLD_CATEGORIES = {"unsupported_true"}
SNIPPET_CHARS = 500


def _gold_passages(question: dict, retriever: Retriever, pages: dict[tuple[str, int], str]) -> list[dict]:
    """The chunk holding each evidence quote. A quote split across chunks gets a passage cut from its page."""
    passages: dict[str, dict] = {}
    for item in question.get("evidence", []):
        quote = normalize(item["quote"])
        match = next((c for c in retriever.chunks if c.publication == item["publication"] and c.page == item["page"] and quote in normalize(c.text)), None)
        if match:
            passages[match.id] = {"id": match.id, "text": match.text}
            continue
        page = pages[(item["publication"], item["page"])]
        words = item["quote"].split()
        start = max(page.find(words[0]), 0)
        passage_id = f"{item['publication']}-p{item['page']}-gold"
        passages[passage_id] = {"id": passage_id, "text": page[max(start - SNIPPET_CHARS, 0) : start + len(item["quote"]) + SNIPPET_CHARS]}
    return list(passages.values())


def build_contexts(questions: list[dict], retriever: Retriever) -> dict[str, dict]:
    """For each question, the real rankings plus the labeled contexts that answer evaluators see.

    with_gold has the evidence plus real distractors. without_gold has only chunks from other pages, so it can't support the answer.
    """
    pages = {(p["publication"], p["page"]): p["text"] for p in load_pages()}
    output = {}
    for question in questions:
        rankings = {mode: [c.id for c in retriever.retrieve(question["question"], mode, k=TOP_K)] for mode in ("dense", "bm25", "hybrid")}
        wide = retriever.retrieve(question["question"], "hybrid", k=30)
        evidence_pages = {(e["publication"], e["page"]) for e in question.get("evidence", [])}
        quotes = [normalize(e["quote"]) for e in question.get("evidence", [])]
        # Rules repeat across pages, so a distractor can't contain the evidence, wherever it's from.
        distractors = [{"id": c.id, "text": c.text} for c in wide if (c.publication, c.page) not in evidence_pages and not any(q in normalize(c.text) for q in quotes)]
        entry = {"rankings": rankings, "without_gold": distractors[:TOP_K]}
        if question["answerable"]:
            gold = _gold_passages(question, retriever, pages)
            entry["gold_ids"] = [p["id"] for p in gold]
            entry["with_gold"] = gold + distractors[: max(TOP_K - len(gold), 0)]
        output[question["id"]] = entry
    return output


def case_context(case: dict, question: dict, contexts: dict[str, dict]) -> list[dict]:
    entry = contexts[question["id"]]
    if not question["answerable"] or case["category"] in NO_GOLD_CATEGORIES:
        return entry["without_gold"]
    return entry["with_gold"]


@dataclass(frozen=True)
class Evaluator:
    name: str
    dimension: str
    kind: str  # local, llm or heuristic
    run: Callable[[dict, dict, list[str], dict], object]


def _evaluators(llm: Callable[[str], str] | None) -> list[Evaluator]:
    """Every answer-level evaluator. Each takes (case, question, context texts, context ids by text)."""
    items = [
        Evaluator("token_support", "faithful", "heuristic", lambda c, q, x, m: faithfulness.token_support(c["answer"], x)),
        Evaluator("number_grounding", "faithful", "heuristic", lambda c, q, x, m: faithfulness.number_grounding(c["answer"], x)),
        Evaluator("sentence_nli", "faithful", "local", lambda c, q, x, m: faithfulness.sentence_nli(c["answer"], x, models.nli)),
        Evaluator("lettucedetect", "faithful", "local", lambda c, q, x, m: faithfulness.span_detector(c["answer"], models.lettuce_spans(x, q["question"], c["answer"]))),
        Evaluator("embedding_relevance", "relevant", "local", lambda c, q, x, m: relevance.embedding_relevance(q["question"], c["answer"], models.embed)),
        Evaluator("cross_encoder_relevance", "relevant", "local", lambda c, q, x, m: relevance.cross_encoder_relevance(q["question"], c["answer"], models.rerank)),
        Evaluator("exact_facts", "correct", "heuristic", lambda c, q, x, m: correctness.exact_facts(c["answer"], q["gold_answer"])),
        Evaluator("token_f1", "correct", "heuristic", lambda c, q, x, m: correctness.token_f1(c["answer"], q["gold_answer"])),
        Evaluator("rouge_l", "correct", "heuristic", lambda c, q, x, m: correctness.rouge_l(c["answer"], q["gold_answer"])),
        Evaluator("bleu", "correct", "heuristic", lambda c, q, x, m: correctness.bleu(c["answer"], q["gold_answer"])),
        Evaluator("embedding_similarity", "correct", "local", lambda c, q, x, m: correctness.embedding_similarity(c["answer"], q["gold_answer"], models.embed)),
        Evaluator("nli_correctness", "correct", "local", lambda c, q, x, m: correctness.nli_correctness(c["answer"], q["gold_answer"], models.nli)),
        Evaluator("key_point_nli", "complete", "local", lambda c, q, x, m: completeness.key_point_nli(c["answer"], q["key_points"], models.nli)),
        Evaluator("key_point_mean", "complete", "local", lambda c, q, x, m: completeness.key_point_mean(c["answer"], q["key_points"], models.nli)),
        Evaluator("abstention_rule", "abstention", "heuristic", lambda c, q, x, m: abstention.abstention_rule(c["answer"], q["answerable"])),
        Evaluator("abstention_reranker", "abstention", "local", lambda c, q, x, m: abstention.abstention_reranker(q["question"], c["answer"], x, models.rerank)),
        Evaluator("citations_exist", "citation", "heuristic", lambda c, q, x, m: citations.citations_exist(citations.extract_citations(c["answer"]), list(m.values()))),
        Evaluator("citation_coverage", "citation", "heuristic", lambda c, q, x, m: citations.citation_coverage(c["answer"])),
        Evaluator("citation_support", "citation", "local", lambda c, q, x, m: citations.citation_support(c["answer"], {v: k for k, v in m.items()}, models.nli)),
    ]
    if llm is not None:
        items += [
            Evaluator("faithfulness_llm", "faithful", "llm", lambda c, q, x, m: faithfulness.faithfulness_llm(q["question"], c["answer"], x, llm)),
            Evaluator("claim_nli", "faithful", "llm", lambda c, q, x, m: faithfulness.claim_nli(c["answer"], x, llm, models.nli)),
            Evaluator("relevance_llm", "relevant", "llm", lambda c, q, x, m: relevance.relevance_llm(q["question"], c["answer"], llm)),
            Evaluator("question_regeneration", "relevant", "llm", lambda c, q, x, m: relevance.question_regeneration(q["question"], c["answer"], llm, models.embed)),
            Evaluator("correctness_llm", "correct", "llm", lambda c, q, x, m: correctness.correctness_llm(q["question"], c["answer"], q["gold_answer"], llm)),
            Evaluator("completeness_llm", "complete", "llm", lambda c, q, x, m: completeness.completeness_llm(q["question"], c["answer"], q["key_points"], llm)),
            Evaluator("abstention_llm", "abstention", "llm", lambda c, q, x, m: abstention.abstention_llm(q["question"], c["answer"], x, llm)),
        ]
    return items


# A gold answer or key points don't exist for an unanswerable question, so those evaluators can't run on it.
NEEDS_GOLD = {"correct", "complete"}


def _applicable(evaluator: Evaluator, case: dict, question: dict, label: bool | None) -> bool:
    if label is None:
        return False
    return not (evaluator.dimension in NEEDS_GOLD and not question["answerable"])


# Temporary API failures produced no answer, so a rerun tries them again. Malformed judge replies stay as errors.
TRANSIENT = ("RateLimitError", "APIConnectionError", "APITimeoutError", "InternalServerError", "RuntimeError: no content")


def _finished(row: dict) -> bool:
    return not (row.get("error") or "").startswith(TRANSIENT)


def _score_one(evaluator: Evaluator, case: dict, question: dict, texts: list[str], ids: dict[str, str], label_value: bool, judge: str | None) -> dict:
    started = time.monotonic()
    row = {"case_id": case["case_id"], "question_id": case["question_id"], "category": case["category"], "origin": case["origin"], "evaluator": evaluator.name, "dimension": evaluator.dimension, "kind": evaluator.kind, "judge": judge, "label_good": label_value}
    try:
        result = evaluator.run(case, question, texts, ids)
        row.update(score=result.score, error=None)
    except Exception as error:  # noqa: BLE001 - every failure is recorded as an error rather than a score
        row.update(score=None, error=f"{type(error).__name__}: {error}"[:300])
    row["seconds"] = time.monotonic() - started
    return row


def run_cases(cases: Iterable[dict], questions: dict[str, dict], contexts: dict[str, dict], labels: dict[str, dict], out: Path, llm: Callable[[str], str] | None = None, judge: str | None = None, only: set[str] | None = None, kinds: set[str] | None = None, threads: int = 15) -> int:
    """Append one row per case and evaluator to `out`, skipping rows already there. Local models run one at a time."""
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            row = json.loads(line)
            if _finished(row):
                done.add((row["case_id"], row["evaluator"], row["judge"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    evaluators = [e for e in _evaluators(llm) if (only is None or e.name in only) and (kinds is None or e.kind in kinds)]
    written = 0
    with out.open("a") as handle:
        parallel: list[tuple] = []
        for case in cases:
            question = questions[case["question_id"]]
            passages = case_context(case, question, contexts)
            texts = [p["text"] for p in passages]
            ids = {p["text"]: p["id"] for p in passages}
            for evaluator in evaluators:
                label = labels[case["category"]][evaluator.dimension]
                row_judge = judge if evaluator.kind == "llm" else None
                if not _applicable(evaluator, case, question, label) or (case["case_id"], evaluator.name, row_judge) in done:
                    continue
                args = (evaluator, case, question, texts, ids, label, row_judge)
                if evaluator.kind == "llm":
                    parallel.append(args)
                else:
                    handle.write(json.dumps(_score_one(*args)) + "\n")
                    written += 1
            handle.flush()
        with ThreadPoolExecutor(threads) as pool:
            for row in pool.map(lambda a: _score_one(*a), parallel):
                handle.write(json.dumps(row) + "\n")
                written += 1
                handle.flush()
    return written
