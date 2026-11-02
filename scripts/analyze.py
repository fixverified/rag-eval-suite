"""Calibrate on dev and report every evaluator: recall by category, false alarms, exploits, ranking quality and errors."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from rag_eval_suite.stats import achieved_fpr, auprc, auroc, cluster_rate, components, question_rate, threshold_for_fpr, threshold_stability
from rag_eval_suite.schema import ALL_LABELS, EXPLOITS

LIBRARY_DIMENSION = {
    "ragas.faithfulness": "faithful", "ragas.response_groundedness": "faithful", "ragas.answer_relevancy": "relevant",
    "ragas.answer_correctness": "correct", "ragas.answer_accuracy": "correct", "ragas.factual_correctness": "correct", "ragas.semantic_similarity": "correct",
    "deepeval.faithfulness": "faithful", "deepeval.hallucination": "faithful", "deepeval.answer_relevancy": "relevant",
    "ragas.context_precision": "context", "ragas.context_precision_no_reference": "context", "ragas.context_recall": "context", "ragas.context_entity_recall": "context", "ragas.context_relevance": "context",
    "deepeval.contextual_precision": "context", "deepeval.contextual_recall": "context", "deepeval.contextual_relevancy": "context",
}
# Version 1 runs only these library metrics. Rows for others are from an interrupted earlier run.
VERSION_1_LIBRARY = {"ragas.faithfulness", "ragas.answer_relevancy", "ragas.answer_correctness", "ragas.context_recall", "deepeval.faithfulness", "deepeval.answer_relevancy", "deepeval.contextual_recall"}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if rows and "evaluator" in rows[0]:
        latest = {(r.get("task_id") or r.get("case_id"), r["evaluator"], r.get("judge")): r for r in rows}
        return list(latest.values())
    return rows


def load_rows(split_dir: Path, score_files: list[Path]) -> list[dict]:
    tasks = {t["task_id"]: t for t in read_jsonl(split_dir / "tasks.jsonl")}
    rows = []
    # A rerun can append a newer row for the same work, so only the last counts.
    for path in score_files:
        for row in read_jsonl(path):
            if "task_id" in row:
                task = tasks[row["task_id"]]
                name = row["evaluator"]
                if name in LIBRARY_DIMENSION and name not in VERSION_1_LIBRARY:
                    continue
                judge = row.get("judge") or (path.stem.split("__")[1].replace("_", "/", 1) if "__" in path.stem else None)
                dimension = LIBRARY_DIMENSION.get(name) or ("context" if task["stage"] == "context" else None)
                if dimension is None or dimension not in task["labels"]:
                    continue
                if task["stage"] == "answer" and ALL_LABELS[task["category"]][dimension] is None:
                    continue
                rows.append({"question_id": task["question_id"], "category": task["category"], "origin": task["origin"], "evaluator": name, "judge": judge, "dimension": dimension, "label_good": task["labels"][dimension], "score": row["score"], "error": row["error"], "variant": task.get("variant")})
            else:
                if ALL_LABELS[row["category"]][row["dimension"]] is not None:
                    rows.append({**row, "variant": None})
    return rows


def key(row: dict) -> str:
    base = row["evaluator"].split("@")[0]
    return f"{base}@{row['judge']}" if row.get("judge") else row["evaluator"]


def page_components(split_dir: Path) -> dict[str, str]:
    questions = read_jsonl(split_dir / "questions.jsonl")
    pages = {q["id"]: [(e["publication"], e["page"]) for e in q.get("evidence", [])] or [("none", int(q["id"].split("-u")[-1]) if "-u" in q["id"] else 0, q["id"])] for q in questions}
    return components(pages)


def is_clean_control(row: dict) -> bool:
    return row["category"].startswith("clean_") or row["category"] == "context_present"


def report(rows: list[dict], component_of: dict[str, str], thresholds: dict[str, float] | None) -> dict:
    grouped = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    output = {}
    for name, items in sorted(grouped.items()):
        errors = [r for r in items if r["score"] is None]
        scored = [r for r in items if r["score"] is not None]
        clean = [r for r in scored if is_clean_control(r) and r["label_good"]]
        bad = [r for r in scored if not r["label_good"]]
        entry = {"dimension": items[0]["dimension"], "rows": len(items), "errors": len(errors), "error_rate": len(errors) / len(items)}
        if clean:
            threshold = thresholds[name] if thresholds else threshold_for_fpr([r["score"] for r in clean])
            flag = lambda r: r["score"] < threshold
            clean_rate = cluster_rate(question_rate((r["question_id"], flag(r)) for r in clean), component_of)
            entry.update(threshold=threshold, clean_questions=clean_rate.questions, fpr=clean_rate.value, fpr_low=clean_rate.low, fpr_high=clean_rate.high, item_fpr=achieved_fpr([r["score"] for r in clean], threshold))
            clean_by_question = defaultdict(list)
            for r in clean:
                clean_by_question[r["question_id"]].append(r["score"])
            if not thresholds:
                entry["threshold_low"], entry["threshold_high"] = threshold_stability(clean_by_question, component_of)
            categories = {}
            for category in sorted({r["category"] for r in bad}):
                group = [r for r in bad if r["category"] == category]
                rate = cluster_rate(question_rate((r["question_id"], flag(r)) for r in group), component_of)
                errored = [r for r in errors if r["category"] == category and not r["label_good"]]
                with_errors = cluster_rate(question_rate([(r["question_id"], flag(r)) for r in group] + [(r["question_id"], False) for r in errored]), component_of)
                categories[category] = {"recall": rate.value, "low": rate.low, "high": rate.high, "questions": rate.questions, "components": rate.components, "recall_errors_as_misses": with_errors.value, "exploit": category in EXPLOITS, "auroc": auroc([r["score"] for r in group], [r["score"] for r in clean]), "auprc": auprc([r["score"] for r in group], [r["score"] for r in clean]), "prevalence": len(group) / (len(group) + len(clean))}
            entry["categories"] = categories
            failures = [r["score"] for r in bad if r["category"] not in EXPLOITS]
            entry["auroc"] = auroc(failures, [r["score"] for r in clean])
            entry["auprc"] = auprc(failures, [r["score"] for r in clean])
        output[name] = entry
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split_dir", type=Path)
    parser.add_argument("scores", nargs="+", type=Path)
    parser.add_argument("--thresholds", type=Path, help="Frozen thresholds. Leave out to calibrate")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = load_rows(args.split_dir, args.scores)
    thresholds = json.loads(args.thresholds.read_text()) if args.thresholds else None
    results = report(rows, page_components(args.split_dir), thresholds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=1))
    print(f"{'evaluator':52} dim         thr    fpr   err  auroc  recall by category")
    for name, entry in results.items():
        cats = " ".join(f"{c[:9]}={v['recall']:.2f}" for c, v in entry.get("categories", {}).items())
        print(f"{name[:52]:52} {entry['dimension'][:10]:10} {entry.get('threshold', float('nan')):5.2f} {entry.get('fpr', float('nan')):5.2f} {entry['error_rate']:5.2f} {entry.get('auroc', float('nan')):5.2f}  {cats}")


if __name__ == "__main__":
    main()
