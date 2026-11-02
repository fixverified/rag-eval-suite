"""Generate real answers on the full test set: chunks, gold removed, closed book and full document."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rag_eval_suite.corpus import build_chunks
from rag_eval_suite.models import LLM
from rag_eval_suite.pipeline import PROMPT, format_passages, generate_closed_book, generate_from_documents

GENERATOR = "z-ai/glm-5.3-flash"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split_dir", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    questions = [json.loads(line) for line in (args.split_dir / "questions.jsonl").read_text().splitlines()]
    contexts = json.loads((args.split_dir / "contexts.json").read_text())
    chunks = {c.id: c for c in build_chunks()}
    llm = LLM(GENERATOR)

    def from_ids(question, ids):
        return llm(PROMPT.format(question=question["question"], passages=format_passages([chunks[i] for i in ids])))

    jobs = []
    for question in questions:
        entry = contexts[question["id"]]
        hybrid = entry["rankings"]["hybrid"]
        jobs.append((question, "chunks", hybrid, lambda q=question, ids=hybrid: from_ids(q, ids)))
        if question["answerable"]:
            removed = [p["id"] for p in entry["without_gold"]]
            jobs.append((question, "gold_removed", removed, lambda q=question, ids=removed: from_ids(q, ids)))
            jobs.append((question, "closed_book", [], lambda q=question: generate_closed_book(q["question"], llm)))
            publications = sorted({e["publication"] for e in question["evidence"]})
            if len(publications) == 1:
                jobs.append((question, "full_document", publications, lambda q=question, p=publications: generate_from_documents(q["question"], p, llm)))

    def run(job):
        question, mode, context_ids, call = job
        try:
            return {"answer_id": f"{question['id']}-{mode}", "question_id": question["id"], "mode": mode, "context_ids": context_ids, "answer": call(), "error": None}
        except Exception as error:  # noqa: BLE001 - recorded rather than dropped
            return {"answer_id": f"{question['id']}-{mode}", "question_id": question["id"], "mode": mode, "context_ids": context_ids, "answer": None, "error": f"{type(error).__name__}: {error}"[:300]}

    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(run, jobs))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(len(rows), "answers;", sum(r["error"] is not None for r in rows), "errors; calls", llm.calls, "cost", round(llm.cost, 4))


if __name__ == "__main__":
    main()
