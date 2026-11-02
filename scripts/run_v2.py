"""Score real generated answers with version 1 evaluators and thresholds, plus the chunks vs. full-document comparison."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evaluators import faithfulness
from rag_eval_suite.corpus import build_chunks, document_text
from rag_eval_suite.harness import _evaluators
from rag_eval_suite.models import LLM, total_cost

JUDGE = "gpt-6-luna"
SKIPPED = {"claim_nli", "question_regeneration", "citations_exist", "citation_coverage", "citation_support"}
NEEDS_CONTEXT = {"faithful", "abstention"}
OUT = Path("data/v2/scores.jsonl")
COMPARISON = Path("data/v2/full_document_scores.jsonl")


def main() -> None:
    questions = {q["id"]: q for q in map(json.loads, Path("data/test_full/questions.jsonl").read_text().splitlines())}
    contexts = json.loads(Path("data/test_full/contexts.json").read_text())
    answers = [a for a in map(json.loads, Path("data/v2/generated.jsonl").read_text().splitlines()) if not a["error"]]
    chunks = {c.id: c.text for c in build_chunks()}
    llm = LLM(JUDGE)
    evaluators = [e for e in _evaluators(llm) if e.name not in SKIPPED]
    done = {(r["answer_id"], r["evaluator"]) for r in map(json.loads, OUT.read_text().splitlines()) if not (r["error"] or "").startswith(("RateLimit", "APIConnection", "APITimeout", "InternalServer"))} if OUT.exists() else set()

    def texts_for(answer):
        return [chunks[i] for i in answer["context_ids"]] if answer["mode"] in ("chunks", "gold_removed") else []

    def score(evaluator, answer):
        question = questions[answer["question_id"]]
        texts = texts_for(answer)
        case = {"answer": answer["answer"]}
        row = {"answer_id": answer["answer_id"], "question_id": answer["question_id"], "mode": answer["mode"], "evaluator": evaluator.name, "dimension": evaluator.dimension, "score": None, "error": None}
        try:
            row["score"] = evaluator.run(case, question, texts, {t: i for t, i in zip(texts, answer["context_ids"])}).score
        except Exception as error:  # noqa: BLE001 - recorded as an error
            row["error"] = f"{type(error).__name__}: {error}"[:300]
        return row

    def applies(evaluator, answer):
        question = questions[answer["question_id"]]
        if evaluator.dimension in ("correct", "complete") and not question["answerable"]:
            return False
        if evaluator.dimension in NEEDS_CONTEXT and answer["mode"] not in ("chunks", "gold_removed"):
            return False
        return (answer["answer_id"], evaluator.name) not in done

    with OUT.open("a") as handle:
        for answer in answers:
            for evaluator in evaluators:
                if evaluator.kind != "llm" and applies(evaluator, answer):
                    handle.write(json.dumps(score(evaluator, answer)) + "\n")
            handle.flush()
        jobs = [(e, a) for a in answers for e in evaluators if e.kind == "llm" and applies(e, a)]
        with ThreadPoolExecutor(15) as pool:
            for row in pool.map(lambda job: score(*job), jobs):
                handle.write(json.dumps(row) + "\n")

    # Each single-publication question gets four cells: answer source by judging source.
    by_id = {a["answer_id"]: a for a in answers}
    cells = []
    for question in questions.values():
        if not question["answerable"]:
            continue
        publications = sorted({e["publication"] for e in question["evidence"]})
        if len(publications) != 1:
            continue
        chunk_answer, document_answer = by_id.get(f"{question['id']}-chunks"), by_id.get(f"{question['id']}-full_document")
        if not chunk_answer or not document_answer:
            continue
        chunk_texts = [chunks[i] for i in chunk_answer["context_ids"]]
        document = [document_text(publications[0])]
        cells += [(question, "chunks", chunk_answer, "chunks", chunk_texts), (question, "chunks", chunk_answer, "document", document), (question, "document", document_answer, "chunks", chunk_texts), (question, "document", document_answer, "document", document)]

    def judge(cell):
        question, generated_from, answer, judged_against, texts = cell
        row = {"question_id": question["id"], "generated_from": generated_from, "judged_against": judged_against, "answer_id": answer["answer_id"], "score": None, "error": None}
        for attempt in range(6):
            try:
                row["score"], row["error"] = faithfulness.faithfulness_llm(question["question"], answer["answer"], texts, llm).score, None
                break
            except Exception as error:  # noqa: BLE001 - recorded as an error
                row["error"] = f"{type(error).__name__}: {error}"[:300]
                # Full publications are large, so these calls can hit a per-minute token limit.
                if "RateLimit" not in row["error"]:
                    break
                time.sleep(30 * (attempt + 1))
        return row

    with ThreadPoolExecutor(2) as pool:
        rows = list(pool.map(judge, cells))
    COMPARISON.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("calls", llm.calls, "cost", round(llm.cost, 3), "total", round(total_cost(), 3))


if __name__ == "__main__":
    main()
