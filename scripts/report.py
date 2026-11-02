"""Build docs/RESULTS.md and results/v1/summary.json from the frozen test run."""

import json
import statistics
from collections import defaultdict
from pathlib import Path

from analyze import load_rows, page_components, read_jsonl, report
from evaluators import retrieval
from rag_eval_suite.stats import wilson

DEV, TEST = Path("data/dev"), Path("data/test_v1")
SCORE_FILES = ["own_local", "own_llm__gpt-6-luna", "own_context__gpt-6-luna", "ragas__gpt-6-luna", "deepeval__gpt-6-luna"]
FLOOR = 30
FAILURES = ["wrong_number", "negation", "wrong_condition", "unsupported_addition", "unsupported_true", "wrongful_answer", "off_topic", "incomplete", "wrongful_refusal", "bad_citation", "context_missing"]
EXPLOITS = ["query_stuffing", "padding", "prompt_injection", "copied_source", "confident_tone", "number_format", "context_number"]
LIBRARY = ("ragas.", "deepeval.")


def files(split: str) -> list[Path]:
    return [Path(f"data/scores/{split}/{name}.jsonl") for name in SCORE_FILES]


def label(name: str) -> str:
    return name.replace("@gpt-6-luna", "")


def cell(entry: dict, category: str) -> str:
    item = entry.get("categories", {}).get(category)
    if not item:
        return "–"
    if entry["threshold"] == 0:
        return "no threshold"
    mark = "*" if item["questions"] < FLOOR else ""
    return f"{item['recall']:.0%}{mark}"


def retrieval_table() -> list[dict]:
    rows = []
    for split, directory in (("dev", DEV), ("test", TEST)):
        questions = [q for q in read_jsonl(directory / "questions.jsonl") if q["answerable"]]
        contexts = json.loads((directory / "contexts.json").read_text())
        tasks = {t["task_id"]: t for t in read_jsonl(directory / "tasks.jsonl")}
        for mode in ("dense", "bm25", "hybrid"):
            scores = defaultdict(list)
            for question in questions:
                ranked, gold = contexts[question["id"]]["rankings"][mode], contexts[question["id"]]["gold_ids"]
                scores["recall"].append(retrieval.recall_at_k(ranked, gold, 5).score)
                scores["mrr"].append(retrieval.mrr(ranked, gold).score)
                scores["ndcg"].append(retrieval.ndcg_at_k(ranked, gold, 5).score)
                scores["all_evidence"].append(float(tasks[f"{question['id']}-{mode}"]["labels"]["context"]))
            rows.append({"split": split, "mode": mode, **{k: statistics.mean(v) for k, v in scores.items()}})
    return rows


def seconds_by_evaluator(split: str) -> dict[str, float]:
    times = defaultdict(list)
    for path in files(split):
        for row in read_jsonl(path):
            if row.get("seconds") is not None:
                times[row["evaluator"]].append(row["seconds"])
    return {name: statistics.median(values) for name, values in times.items()}


def main() -> None:
    thresholds = json.loads(Path("results/v1/thresholds.json").read_text())
    # Library context metrics need a gold answer, so every context evaluator is compared on answerable questions only.
    answerable_only = lambda rows: [r for r in rows if not (r["dimension"] == "context" and "-u" in r["question_id"])]
    test_rows = answerable_only(load_rows(TEST, files("test_v1")))
    components = page_components(TEST)
    frozen = report(test_rows, components, thresholds)
    defaults = report(test_rows, components, {name: 0.5 for name in frozen})
    dev_rows = answerable_only(load_rows(DEV, files("dev")))
    dev = report(dev_rows, page_components(DEV), None)
    seconds = seconds_by_evaluator("test_v1")
    retrieval_rows = retrieval_table()
    summary = {"frozen": frozen, "library_at_0_5": {k: v for k, v in defaults.items() if k.startswith(LIBRARY)}, "dev": dev, "retrieval": retrieval_rows, "median_seconds": seconds}
    Path("results/v1/summary.json").write_text(json.dumps(summary, indent=1))

    def matrix(columns: list[str]) -> list[str]:
        header = ["Evaluator", "Dimension", "False alarms", *[c.replace("_", " ") for c in columns]]
        lines = ["| " + " | ".join(header) + " |", "|---|---|" + "---:|" * (len(header) - 2)]
        for dimension in ("faithful", "correct", "relevant", "complete", "abstention", "citation", "context"):
            for name, entry in frozen.items():
                if entry["dimension"] == dimension and "fpr" in entry:
                    lines.append(f"| `{label(name)}` | {dimension} | {entry['fpr']:.0%} | " + " | ".join(cell(entry, c) for c in columns) + " |")
        return lines

    text = ["# Results", "", "Version 1. All figures come from the sealed test set, run once with thresholds, prompts and versions frozen on dev. Recall is the share of known-bad answers flagged. False alarms are clean controls wrongly flagged. Both are at question level.", "", "Most categories have 30 questions, and some have 14–29. With 30, a perfect 100% still has a 95% lower bound near 89%, and 0% false alarms an upper bound near 11%. A `*` marks fewer than 30 questions, which is exploratory. A `–` means that evaluator wasn't scored on that failure, by the [scope table](SCOPE.md). `no threshold` means holding false alarms to 5% on dev required a threshold of 0, so the evaluator can flag nothing there, though its AUROC below may still be high. Context evaluators are compared on the 30 answerable questions.\n\nEvery case is injected, and clean controls derive from gold answers. False alarms therefore say nothing about real model answers. Test cases were written by a separate agent and kept out of dev work, but the builder and assistant knew the failure categories and exploit families, so this isn't full blinding.", "", "## Failures", ""]
    text += matrix(FAILURES)
    text += ["", "## Exploits", "", "Copied source, confident tone, number format and context number were held out of dev entirely.", ""]
    text += matrix(EXPLOITS)
    text += ["", "## Ranking quality and reliability", "", "| Evaluator | Threshold | AUROC | AUPRC | False alarms, 95% interval | Errors | Median seconds |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, entry in frozen.items():
        if "fpr" in entry:
            time = seconds.get(name.split("@")[0])
            text.append(f"| `{label(name)}` | {entry['threshold']:.2f} | {entry['auroc']:.2f} | {entry['auprc']:.2f} | {wilson(entry['fpr'] * entry['clean_questions'], entry['clean_questions'])[0]:.0%}–{wilson(entry['fpr'] * entry['clean_questions'], entry['clean_questions'])[1]:.0%} | {entry['errors']}/{entry['rows']} | {'' if time is None else f'{time:.2f}'} |")
    text += ["", "## Ragas and DeepEval at a 0.5 threshold", "", "These runs use a threshold of 0.5 rather than the dev-calibrated one. 0.5 is DeepEval's default. Ragas ships no threshold, so 0.5 is our choice.", "", "| Metric | False alarms | Failure recall, mean across categories |", "|---|---:|---:|"]
    for name, entry in summary["library_at_0_5"].items():
        if "fpr" in entry:
            values = [v["recall"] for c, v in entry["categories"].items() if not v["exploit"]]
            text.append(f"| `{label(name)}` | {entry['fpr']:.0%} | {statistics.mean(values):.0%} |")
    text += ["", "## Retrieval modes", "", "These describe the sample pipeline's modes and don't test an evaluator, since gold labels define these metrics. All evidence means every gold quote appears in the top 5.", "", "| Split | Mode | Recall@5 | MRR | nDCG@5 | All evidence |", "|---|---|---:|---:|---:|---:|"]
    for row in retrieval_rows:
        text.append(f"| {row['split']} | {row['mode']} | {row['recall']:.2f} | {row['mrr']:.2f} | {row['ndcg']:.2f} | {row['all_evidence']:.0%} |")
    text += ["", "## Not run in version 1", "", "Real generated answers as clean controls or failures, document-shift set, GLM judge comparison, `claim_nli`, `question_regeneration`, real generated-answer failures, memory control and synthetic corpus, chunks vs. full-document comparison, repeat-run reliability, external datasets, and the Ragas and DeepEval metrics outside `ragas.faithfulness`, `ragas.answer_relevancy`, `ragas.answer_correctness`, `ragas.context_recall`, `deepeval.faithfulness`, `deepeval.answer_relevancy` and `deepeval.contextual_recall`. No pairwise significance tests or cluster-bootstrap reporting were included, intervals shown are Wilson intervals at question level, and dollar cost per evaluator wasn't measured. Close differences aren't findings.", ""]
    Path("docs/RESULTS.md").write_text("\n".join(text))
    print("ok")


if __name__ == "__main__":
    main()
