"""Run this repo's context evaluators on a split's context tasks."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evaluators import context
from rag_eval_suite import models


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--judge", required=True)
    parser.add_argument("--questions", type=int)
    args = parser.parse_args()
    tasks = [t for t in map(json.loads, args.tasks.read_text().splitlines()) if t["stage"] == "context"]
    if args.questions:
        keep = sorted({t["question_id"] for t in tasks})[: args.questions]
        tasks = [t for t in tasks if t["question_id"] in keep]
    llm = models.LLM(args.judge)
    done = {(r["task_id"], r["evaluator"]) for r in map(json.loads, args.out.read_text().splitlines())} if args.out.exists() else set()

    def row(task, name, score=None, error=None):
        return {"task_id": task["task_id"], "evaluator": name, "score": score, "error": error}

    def judge(task):
        try:
            return row(task, f"context_sufficiency_llm@{args.judge}", context.context_sufficiency_llm(task["question"], task["contexts"], llm).score)
        except Exception as error:  # noqa: BLE001 - recorded as an error
            return row(task, f"context_sufficiency_llm@{args.judge}", error=f"{type(error).__name__}: {error}"[:300])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a") as handle:
        for task in tasks:
            if (task["task_id"], "context_relevance_reranker") not in done:
                handle.write(json.dumps(row(task, "context_relevance_reranker", context.context_relevance_reranker(task["question"], task["contexts"], models.rerank).score)) + "\n")
            if (task["task_id"], "signal_ratio") not in done:
                handle.write(json.dumps(row(task, "signal_ratio", context.signal_ratio(task["question"], task["contexts"], models.rerank).score)) + "\n")
        pending = [t for t in tasks if (t["task_id"], f"context_sufficiency_llm@{args.judge}") not in done]
        with ThreadPoolExecutor(15) as pool:
            for result in pool.map(judge, pending):
                handle.write(json.dumps(result) + "\n")
                handle.flush()
    print("calls", llm.calls, "cost", round(llm.cost, 4), "total", round(models.total_cost(), 4))


if __name__ == "__main__":
    main()
