"""Report version 2: evaluators on real answers at frozen thresholds, generator accuracy, and chunks vs. full document."""

import json
import statistics
from collections import defaultdict
from pathlib import Path

from rag_eval_suite.stats import wilson

J = "@gpt-6-luna"
LIBRARY_DIMENSION = {"ragas.faithfulness": "faithful", "ragas.answer_relevancy": "relevant", "ragas.answer_correctness": "correct", "deepeval.faithfulness": "faithful", "deepeval.answer_relevancy": "relevant"}
LLM_NAMES = {"faithfulness_llm", "relevance_llm", "correctness_llm", "completeness_llm", "abstention_llm"}


def read(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def rate(flags: list[bool]) -> str:
    if not flags:
        return "–"
    low, high = wilson(sum(flags), len(flags))
    return f"{sum(flags)}/{len(flags)} ({sum(flags) / len(flags):.0%}, {low:.0%}–{high:.0%})"


def main() -> None:
    thresholds = json.loads(Path("results/v1/thresholds.json").read_text())
    labels = {r["answer_id"]: r for r in read("data/v2/labels_final.jsonl")}
    answers = {a["answer_id"]: a for a in read("data/v2/generated.jsonl")}
    questions = {q["id"]: q for q in read("data/test_full/questions.jsonl")}
    fresh = lambda question_id: int(question_id.split("-")[1][1:]) > (30 if "-a" in question_id else 20)

    rows = []
    for row in read("data/v2/scores.jsonl"):
        name = f"{row['evaluator']}{J}" if row["evaluator"] in LLM_NAMES else row["evaluator"]
        rows.append({**row, "key": name})
    for path in ("data/v2/ragas__gpt-6-luna.jsonl", "data/v2/deepeval__gpt-6-luna.jsonl"):
        for row in read(path):
            if row["evaluator"] in LIBRARY_DIMENSION:
                rows.append({"answer_id": row["task_id"], "question_id": answers[row["task_id"]]["question_id"], "mode": answers[row["task_id"]]["mode"], "evaluator": row["evaluator"], "dimension": LIBRARY_DIMENSION[row["evaluator"]], "score": row["score"], "error": row["error"], "key": f"{row['evaluator']}{J}"})

    grouped = defaultdict(list)
    for row in rows:
        label = labels.get(row["answer_id"], {}).get(row["dimension"])
        if label is not None:
            grouped[(row["dimension"], row["key"])].append({**row, "label": label})
    summary = {}
    lines = ["| Evaluator | Dimension | Threshold | Real failures flagged | Real good answers flagged | Errors |", "|---|---|---:|---:|---:|---:|"]
    for (dimension, key), items in sorted(grouped.items()):
        if key not in thresholds:
            continue
        threshold = thresholds[key]
        scored = [r for r in items if r["score"] is not None]
        bad = [r["score"] < threshold for r in scored if not r["label"]]
        good = [r["score"] < threshold for r in scored if r["label"]]
        fresh_bad = [r["score"] < threshold for r in scored if not r["label"] and fresh(r["question_id"])]
        fresh_good = [r["score"] < threshold for r in scored if r["label"] and fresh(r["question_id"])]
        errors = len(items) - len(scored)
        summary[key] = {"dimension": dimension, "threshold": threshold, "bad": sum(bad), "bad_total": len(bad), "good": sum(good), "good_total": len(good), "fresh_bad": sum(fresh_bad), "fresh_bad_total": len(fresh_bad), "fresh_good": sum(fresh_good), "fresh_good_total": len(fresh_good), "errors": errors}
        shown = "no threshold" if threshold == 0 else None
        library_errors = sum(1 for r in rows if r["key"] == key and r["score"] is None)
        lines.append(f"| `{key.replace(J, '')}` | {dimension} | {threshold:.4f} | {shown or rate(bad)} | {shown or rate(good)} | {library_errors} |")

    # A null relevance label marks a refusal. Refusals are easy for any similarity metric, so wrong non-refusals are shown too.
    # Only retrieval-based answers count here, the pool every evaluator saw, including Ragas.
    is_refusal = lambda answer_id: labels[answer_id]["relevant"] is None
    wrong_answers = {}
    for (dimension, key), items in grouped.items():
        if dimension == "correct" and key in thresholds:
            flags = [r["score"] < thresholds[key] for r in items if r["score"] is not None and not r["label"] and not is_refusal(r["answer_id"]) and r["mode"] in ("chunks", "gold_removed")]
            refusals = [r["score"] < thresholds[key] for r in items if r["score"] is not None and not r["label"] and is_refusal(r["answer_id"])]
            good_in_chunks = [r["score"] < thresholds[key] for r in items if r["score"] is not None and r["label"] and r["mode"] == "chunks"]
            wrong_answers[key] = {"wrong_flagged": sum(flags), "wrong_total": len(flags), "refusals_flagged": sum(refusals), "refusals_total": len(refusals), "good_chunks_flagged": sum(good_in_chunks), "good_chunks_total": len(good_in_chunks)}

    generator = []
    for mode in ("closed_book", "chunks", "gold_removed", "full_document"):
        modes = [labels[a] for a, r in answers.items() if r["mode"] == mode and a in labels and questions[r["question_id"]]["answerable"]]
        correct = [r["correct"] for r in modes if r["correct"] is not None]
        generator.append({"mode": mode, "answerable_correct": sum(correct), "answerable_total": len(correct), "unfaithful": sum(r["faithful"] is False for r in modes)})
    unanswerable = [labels[a] for a, r in answers.items() if r["mode"] == "chunks" and a in labels and not questions[r["question_id"]]["answerable"]]
    declined = sum(r["abstention"] is True for r in unanswerable)

    paired = []
    for question in questions.values():
        chunk_id, document_id = f"{question['id']}-chunks", f"{question['id']}-full_document"
        if chunk_id in labels and document_id in labels and labels[chunk_id]["correct"] is not None and labels[document_id]["correct"] is not None:
            paired.append((labels[chunk_id]["correct"], labels[document_id]["correct"], is_refusal(chunk_id)))
    paired_summary = {"questions": len(paired), "chunks_correct": sum(p[0] for p in paired), "document_correct": sum(p[1] for p in paired), "only_document_correct": sum(p[1] and not p[0] for p in paired), "only_chunks_correct": sum(p[0] and not p[1] for p in paired), "chunk_refusals_where_document_correct": sum(p[1] and not p[0] and p[2] for p in paired)}

    cells = defaultdict(list)
    for row in read("data/v2/full_document_scores.jsonl"):
        cells[(row["generated_from"], row["judged_against"])].append(row)
    frozen = thresholds[f"faithfulness_llm{J}"]
    comparison = []
    # Compare only questions scored in all four cells.
    complete_cells = defaultdict(int)
    for row in read("data/v2/full_document_scores.jsonl"):
        complete_cells[row["question_id"]] += row["score"] is not None
    paired_questions = {q for q, count in complete_cells.items() if count == 4}
    for key, items in sorted(cells.items()):
        scored = [r["score"] for r in items if r["score"] is not None and r["question_id"] in paired_questions]
        comparison.append({"generated_from": key[0], "judged_against": key[1], "questions": len(scored), "mean": statistics.mean(scored), "flagged": sum(s < frozen for s in scored), "errors": sum(r["score"] is None for r in items)})
    disagreement = []
    by_answer = defaultdict(dict)
    for row in read("data/v2/full_document_scores.jsonl"):
        by_answer[(row["question_id"], row["generated_from"])][row["judged_against"]] = row["score"]
    for (question, source), pair in by_answer.items():
        if question not in paired_questions or None in pair.values() or len(pair) < 2:
            continue
        if pair["chunks"] < frozen <= pair["document"]:
            disagreement.append(source)

    Path("results/v2").mkdir(parents=True, exist_ok=True)
    Path("results/v2/summary.json").write_text(json.dumps({"evaluators": summary, "generator": generator, "unanswerable_declined": [declined, len(unanswerable)], "comparison": comparison, "supported_by_document_only": {"chunks": disagreement.count("chunks"), "document": disagreement.count("document")}, "correctness_detail": wrong_answers, "paired_chunks_vs_document": paired_summary}, indent=1))
    text = ["# Version 2 results", "", "Real answers from `z-ai/glm-5.3-flash` on all 100 test questions, added after version 1 was public. Version 1 thresholds and prompts are unchanged. Two AI agents labeled answers without seeing scores, and a third settled their 5 disagreements out of about 1,000 labels. No human has reviewed these labels.", "", "Ragas and DeepEval ran only on chunk and evidence-removed answers, so they have fewer rows than other evaluators in the table below. Answers are reused across modes, so these counts aren't independent questions. Ranges are 95% Wilson intervals at answer level, which makes them too narrow where answers cluster by question.", "", "## Results on questions unused in version 1", "", "These 30 answerable and 20 unanswerable questions weren't in version 1's cases, so they're a cleaner check, though the same thresholds and judge apply.", "", "| Evaluator | Real failures flagged | Real good answers flagged |", "|---|---:|---:|", *[f"| `{k.replace(J, '')}` | {v['fresh_bad']}/{v['fresh_bad_total']} | {v['fresh_good']}/{v['fresh_good_total']} |" for k, v in sorted(summary.items()) if v['threshold'] != 0], "", "## How the generator did", "", "| Mode | Answerable answers correct | Answers unsupported by their context |", "|---|---:|---:|"]
    for row in generator:
        support = "–" if row["mode"] == "closed_book" else row["unfaithful"]
        text.append(f"| {row['mode'].replace('_', ' ')} | {row['answerable_correct']}/{row['answerable_total']} | {support} |")
    text += ["", f"With retrieved chunks, it handled {declined} of {len(unanswerable)} unanswerable questions correctly.", "", "## Evaluators on real answers", "", *lines, "", "## Correctness: refusals vs. wrong answers", "", "Most real failures here are refusals, which any similarity metric catches. This table separates them, using only answers from chunks or evidence-removed context, which every evaluator saw. Wrong answers include partial ones, mostly correct answers that declined part of a question.", "", "| Evaluator | Wrong or partial non-refusals flagged | Refusals on answerable questions flagged | Good chunk answers flagged |", "|---|---:|---:|---:|", *[f"| `{key.replace(J, '')}` | {d['wrong_flagged']}/{d['wrong_total']} | {d['refusals_flagged']}/{d['refusals_total']} | {d['good_chunks_flagged']}/{d['good_chunks_total']} |" for key, d in sorted(wrong_answers.items())], "", "## Chunks vs. full document", "", "Each cell scores answers with `faithfulness_llm`. Flagged means below the frozen threshold.", "", "| Generated from | Judged against | Questions | Mean score | Flagged | Errors |", "|---|---|---:|---:|---:|---:|"]
    for row in comparison:
        text.append(f"| {row['generated_from']} | {row['judged_against']} | {row['questions']} | {row['mean']:.2f} | {row['flagged']} | {row['errors']} |")
    text += ["", f"On the same {paired_summary['questions']} single-publication questions, chunks produced {paired_summary['chunks_correct']} correct answers and the full publication {paired_summary['document_correct']}. The document was right and chunks wrong on {paired_summary['only_document_correct']} questions, {paired_summary['chunk_refusals_where_document_correct']} of them chunk refusals. The reverse happened on {paired_summary['only_chunks_correct']}. Refusals count in these cells, and `faithfulness_llm` isn't designed to score them, so the chunks-judged-against-document cell mixes refusals with real unsupported claims."]
    text += ["", f"Answers flagged against chunks but not against the document: {disagreement.count('chunks')} generated from chunks, {disagreement.count('document')} generated from the document.", ""]
    Path("docs/RESULTS_V2.md").write_text("\n".join(text))
    print("\n".join(text))


if __name__ == "__main__":
    main()
