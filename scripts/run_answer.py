"""Run this repo's answer-level evaluators on a split's cases."""

import argparse
import json
from pathlib import Path

from rag_eval_suite.harness import run_cases
from rag_eval_suite.models import LLM, total_cost
from rag_eval_suite.schema import ALL_LABELS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split_dir", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--judge")
    parser.add_argument("--kinds", nargs="+")
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--questions", type=int, help="Use only the first N answerable and N unanswerable questions")
    parser.add_argument("--cases-file", default="cases.jsonl")
    args = parser.parse_args()
    questions = {q["id"]: q for q in map(json.loads, (args.split_dir / "questions.jsonl").read_text().splitlines())}
    contexts = json.loads((args.split_dir / "contexts.json").read_text())
    cases = [json.loads(line) for line in (args.split_dir / args.cases_file).read_text().splitlines()]
    if args.questions:
        keep = {q for flag in (True, False) for q in [i for i, row in questions.items() if row["answerable"] == flag][: args.questions]}
        cases = [c for c in cases if c["question_id"] in keep]
    llm = LLM(args.judge) if args.judge else None
    written = run_cases(cases, questions, contexts, ALL_LABELS, args.out, llm=llm, judge=args.judge, only=set(args.only) if args.only else None, kinds=set(args.kinds) if args.kinds else None)
    print(f"wrote {written} rows; calls {getattr(llm, 'calls', 0)}, cached {getattr(llm, 'cached', 0)}, this run ${getattr(llm, 'cost', 0):.4f}, total ${total_cost():.4f}")


if __name__ == "__main__":
    main()
