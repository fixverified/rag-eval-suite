"""Measure repeat-run reliability of the LLM judges, then cross-validate thresholds on real answers."""

import json
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evaluators import correctness, faithfulness
from rag_eval_suite.corpus import build_chunks
from rag_eval_suite.models import LLM, total_cost
from rag_eval_suite.stats import auroc, threshold_for_fpr

JUDGE = "gpt-6-luna"
SEEDS = [101, 102, 103, 104, 105]
FOLDS = 5
J = "@gpt-6-luna"
CORRECTNESS = ["bleu", "correctness_llm", "embedding_similarity", "exact_facts", "nli_correctness", "rouge_l", "token_f1", "ragas.answer_correctness"]
REPEATS = Path("data/v3/repeats.jsonl")


def read(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def run_repeats(questions: dict, answers: list[dict], chunks: dict) -> None:
    jobs = []
    for seed in SEEDS:
        llm = LLM(JUDGE, seed=seed)
        for answer in answers:
            question = questions[answer["question_id"]]
            texts = [chunks[i] for i in answer["context_ids"]]
            jobs.append((seed, "faithfulness_llm", answer, lambda q=question, a=answer, x=texts, m=llm: faithfulness.faithfulness_llm(q["question"], a["answer"], x, m)))
            if question["answerable"]:
                jobs.append((seed, "correctness_llm", answer, lambda q=question, a=answer, m=llm: correctness.correctness_llm(q["question"], a["answer"], q["gold_answer"], m)))

    def run(job):
        seed, evaluator, answer, call = job
        row = {"seed": seed, "evaluator": evaluator, "answer_id": answer["answer_id"], "score": None, "error": None}
        try:
            row["score"] = call().score
        except Exception as error:  # noqa: BLE001 - recorded as an error
            row["error"] = f"{type(error).__name__}: {error}"[:300]
        return row

    with ThreadPoolExecutor(15) as pool:
        rows = list(pool.map(run, jobs))
    REPEATS.parent.mkdir(parents=True, exist_ok=True)
    REPEATS.write_text("".join(json.dumps(r) + "\n" for r in rows))


def repeat_summary(thresholds: dict, labels: dict) -> dict:
    output = {}
    grouped = defaultdict(lambda: defaultdict(list))
    errors = defaultdict(int)
    for row in read(str(REPEATS)):
        if row["score"] is None:
            errors[row["evaluator"]] += 1
        else:
            grouped[row["evaluator"]][row["answer_id"]].append(row["score"])
    for evaluator, items in grouped.items():
        threshold = thresholds[f"{evaluator}{J}"]
        complete = {a: s for a, s in items.items() if len(s) == len(SEEDS)}
        verdict_changed = sum(len({v < threshold for v in s}) > 1 for s in complete.values())
        rating_changed = sum(len(set(s)) > 1 for s in complete.values())
        dimension = {"faithfulness_llm": "faithful", "correctness_llm": "correct"}[evaluator]
        labeled = {a: s for a, s in complete.items() if labels.get(a, {}).get(dimension) is not None}
        flagged_good = [sum(v < threshold for v in s) / len(s) for a, s in labeled.items() if labels[a][dimension]]
        flagged_bad = [sum(v < threshold for v in s) / len(s) for a, s in labeled.items() if not labels[a][dimension]]
        output[evaluator] = {"threshold": threshold, "answers": len(complete), "runs": len(SEEDS), "verdict_changed": verdict_changed, "rating_changed": rating_changed, "errors": errors[evaluator], "good_answers": len(flagged_good), "mean_good_flagged": sum(flagged_good) / max(len(flagged_good), 1), "bad_answers": len(flagged_bad), "mean_bad_flagged": sum(flagged_bad) / max(len(flagged_bad), 1)}
    return output


def calibration(labels: dict, answers: dict) -> dict:
    rows = defaultdict(dict)
    for row in read("data/v2/scores.jsonl"):
        if row["evaluator"] in CORRECTNESS and row["score"] is not None and row["mode"] in ("chunks", "gold_removed"):
            rows[row["evaluator"]][row["answer_id"]] = row["score"]
    for row in read("data/v2/ragas__gpt-6-luna.jsonl"):
        if row["evaluator"] == "ragas.answer_correctness" and row["score"] is not None:
            rows[row["evaluator"]][row["task_id"]] = row["score"]
    question_ids = sorted({answers[a]["question_id"] for a in rows["bleu"]})
    random.Random(20261104).shuffle(question_ids)
    fold_of = {q: i % FOLDS for i, q in enumerate(question_ids)}
    output = {}
    for evaluator, scores in rows.items():
        usable = {a: s for a, s in scores.items() if labels.get(a, {}).get("correct") is not None}
        result = {"good_flagged": 0, "good_total": 0, "wrong_flagged": 0, "wrong_total": 0, "refusals_flagged": 0, "refusals_total": 0, "thresholds": []}
        for fold in range(FOLDS):
            train = [s for a, s in usable.items() if labels[a]["correct"] and fold_of[answers[a]["question_id"]] != fold]
            threshold = threshold_for_fpr(train)
            result["thresholds"].append(threshold)
            for answer, score in usable.items():
                if fold_of[answers[answer]["question_id"]] != fold:
                    continue
                flagged = score < threshold
                if labels[answer]["correct"]:
                    result["good_total"] += 1
                    result["good_flagged"] += flagged
                elif labels[answer]["relevant"] is None:
                    result["refusals_total"] += 1
                    result["refusals_flagged"] += flagged
                else:
                    result["wrong_total"] += 1
                    result["wrong_flagged"] += flagged
        wrong = [s for a, s in usable.items() if not labels[a]["correct"] and labels[a]["relevant"] is not None]
        good = [s for a, s in usable.items() if labels[a]["correct"]]
        result["auroc_wrong_vs_good"] = auroc(wrong, good)
        output[evaluator] = result
    return output


def main() -> None:
    questions = {q["id"]: q for q in read("data/test_full/questions.jsonl")}
    generated = [a for a in read("data/v2/generated.jsonl") if not a["error"] and a["mode"] in ("chunks", "gold_removed")]
    chunks = {c.id: c.text for c in build_chunks()}
    labels = {r["answer_id"]: r for r in read("data/v2/labels_final.jsonl")}
    thresholds = json.loads(Path("results/v1/thresholds.json").read_text())
    if not REPEATS.exists():
        run_repeats(questions, generated, chunks)
    repeats = repeat_summary(thresholds, labels)
    calibrated = calibration(labels, {a["answer_id"]: a for a in generated})
    Path("results/v3").mkdir(parents=True, exist_ok=True)
    Path("results/v3/summary.json").write_text(json.dumps({"repeats": repeats, "calibration": calibrated}, indent=1))
    text = ["# Version 3 results", "", "Added after version 2. Both analyses use real answers from chunks or evidence-removed context, with version 2's AI labels. No human has reviewed these labels.", "", "## Do LLM verdicts change between runs?", "", f"Each answer was judged {len(SEEDS)} times by `gpt-6-luna` at temperature 1, using different seeds. Verdicts use the version 1 thresholds.", "", "| Evaluator | Answers | Verdict changed | Rating changed | Good answers flagged, mean | Bad answers flagged, mean | Errors |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, row in sorted(repeats.items()):
        text.append(f"| `{name}` | {row['answers']} | {row['verdict_changed']} ({row['verdict_changed'] / row['answers']:.0%}) | {row['rating_changed']} ({row['rating_changed'] / row['answers']:.0%}) | {row['mean_good_flagged']:.0%} | {row['mean_bad_flagged']:.0%} | {row['errors']} |")
    text += ["", "## Do better thresholds fix the cheap metrics?", "", "Each evaluator's threshold was set on real good answers in 4 folds to allow at most 5% false alarms, then scored on the fifth, by question. Sample sizes are small, and AUROC here compares wrong or partial non-refusals with good answers, without thresholds.", "", "| Evaluator | Good answers flagged | Wrong or partial answers caught | Refusals caught | AUROC |", "|---|---:|---:|---:|---:|"]
    for name, row in sorted(calibrated.items(), key=lambda item: -item[1]["auroc_wrong_vs_good"]):
        text.append(f"| `{name}` | {row['good_flagged']}/{row['good_total']} | {row['wrong_flagged']}/{row['wrong_total']} | {row['refusals_flagged']}/{row['refusals_total']} | {row['auroc_wrong_vs_good']:.2f} |")
    text.append("")
    Path("docs/RESULTS_V3.md").write_text("\n".join(text))
    print("\n".join(text))
    print("total tracked", round(total_cost(), 3))


if __name__ == "__main__":
    main()
