"""Write a stratified, shuffled sheet of cases for human label review. It shows no evaluator scores or expected labels."""

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

SEED = 20261103
PER_CATEGORY = 6
QUESTIONS_REVIEWED = 12
OUT = Path("review")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    rows, key = [], []
    for directory in ("data/dev", "data/test_v1"):
        questions = {q["id"]: q for q in map(json.loads, Path(directory, "questions.jsonl").read_text().splitlines())}
        cases = defaultdict(list)
        for case in map(json.loads, Path(directory, "cases.jsonl").read_text().splitlines()):
            cases[case["category"]].append(case)
        for category, group in sorted(cases.items()):
            for case in rng.sample(group, min(PER_CATEGORY // 2 + 1, len(group))):
                question = questions[case["question_id"]]
                evidence = " || ".join(f"{e['publication']} p{e['page']}: {e['quote']}" for e in question.get("evidence", []))
                rows.append({"question": question["question"], "gold_answer": question.get("gold_answer", "(no answer in the corpus)"), "evidence": evidence, "answer": case["answer"], "is_answer_good (yes/no)": "", "notes": ""})
                key.append({"category": category, "case_id": case["case_id"]})
    order = list(range(len(rows)))
    rng.shuffle(order)
    with (OUT / "label_review.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row", *rows[0]])
        writer.writeheader()
        for number, index in enumerate(order, 1):
            writer.writerow({"row": number, **rows[index]})
    (OUT / "label_review_key.json").write_text(json.dumps([{**key[i], "row": n} for n, i in enumerate(order, 1)], indent=1))
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
