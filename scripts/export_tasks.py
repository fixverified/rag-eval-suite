"""Write a split's answer and context tasks in the format every library runner reads."""

import argparse
import json
from pathlib import Path

from rag_eval_suite.corpus import normalize
from rag_eval_suite.harness import case_context
from rag_eval_suite.pipeline import Retriever
from rag_eval_suite.schema import ALL_LABELS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split_dir", type=Path)
    parser.add_argument("--modes", nargs="+", default=["dense", "bm25", "hybrid"])
    args = parser.parse_args()
    questions = {q["id"]: q for q in map(json.loads, (args.split_dir / "questions.jsonl").read_text().splitlines())}
    cases = [json.loads(line) for line in (args.split_dir / "cases.jsonl").read_text().splitlines()]
    contexts = json.loads((args.split_dir / "contexts.json").read_text())
    retriever = Retriever()
    with (args.split_dir / "tasks.jsonl").open("w") as handle:
        for case in cases:
            question = questions[case["question_id"]]
            labels = {k: v for k, v in ALL_LABELS[case["category"]].items() if v is not None}
            handle.write(json.dumps({"task_id": case["case_id"], "stage": "answer", "question_id": question["id"], "question": question["question"], "answer": case["answer"], "contexts": [p["text"] for p in case_context(case, question, contexts)], "gold": question.get("gold_answer"), "labels": labels, "category": case["category"], "origin": case["origin"]}) + "\n")
        for question in questions.values():
            entry = contexts[question["id"]]
            quotes = [normalize(e["quote"]) for e in question.get("evidence", [])]
            variants = {mode: [retriever.by_id[i].text for i in entry["rankings"][mode]] for mode in args.modes}
            if question["answerable"]:
                variants["gold_present"] = [p["text"] for p in entry["with_gold"]]
            variants["gold_removed"] = [p["text"] for p in entry["without_gold"]]
            for name, texts in variants.items():
                joined = normalize(" ".join(texts))
                present = bool(quotes) and all(q in joined for q in quotes)
                handle.write(json.dumps({"task_id": f"{question['id']}-{name}", "stage": "context", "question_id": question["id"], "variant": name, "question": question["question"], "answer": question.get("gold_answer"), "contexts": texts, "gold": question.get("gold_answer"), "labels": {"context": present}, "category": "context_present" if present else "context_missing", "origin": "real" if name in args.modes else "constructed"}) + "\n")


if __name__ == "__main__":
    main()
