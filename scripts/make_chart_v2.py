"""Build docs/results_v2.html: planted vs. real behavior of correctness evaluators at frozen thresholds."""

import json
from pathlib import Path

V2 = json.loads(Path("results/v2/summary.json").read_text())
J = "@gpt-6-luna"
ROWS = [("LLM judge", f"correctness_llm{J}"), ("Ragas correctness", f"ragas.answer_correctness{J}"), ("BLEU", "bleu"), ("Exact facts", "exact_facts"), ("NLI", "nli_correctness"), ("ROUGE-L", "rouge_l"), ("Token F1", "token_f1"), ("Embedding similarity", "embedding_similarity")]


def planted_rates() -> dict[str, float]:
    tasks = {t["task_id"]: t for t in map(json.loads, Path("data/test_v1/tasks.jsonl").read_text().splitlines())}
    thresholds = json.loads(Path("results/v1/thresholds.json").read_text())
    rates = {}
    for name, key in ROWS:
        evaluator = key.split("@")[0]
        scores = []
        for file in ("own_local", "own_llm__gpt-6-luna", "ragas__gpt-6-luna"):
            for row in map(json.loads, Path(f"data/scores/test_v1/{file}.jsonl").read_text().splitlines()):
                category = row.get("category") or tasks.get(row.get("task_id"), {}).get("category")
                if row["evaluator"] == evaluator and category in ("clean_paraphrase", "clean_longer") and row["score"] is not None:
                    scores.append(row["score"] < thresholds[key])
        rates[key] = sum(scores) / len(scores)
    return rates


PLANTED = planted_rates()


def good(value: float) -> str:
    return f"background:rgba(70,224,181,{0.08 + 0.80 * value:.2f});color:{'#07130F' if value >= 0.55 else '#F4F6F9'}"


def bad(value: float) -> str:
    return f"background:rgba(255,155,84,{0.08 + 0.85 * value:.2f});color:{'#1B0E05' if value >= 0.55 else '#F4F6F9'}"


body = ""
for name, key in ROWS:
    detail = V2["correctness_detail"][key]
    planted = PLANTED[key]
    real = detail["good_chunks_flagged"] / detail["good_chunks_total"]
    caught = detail["wrong_flagged"] / detail["wrong_total"]
    body += f'<tr><th>{name}</th><td style="{bad(planted)}">{planted:.0%}</td><td style="{bad(real)}">{real:.0%}<small>{detail["good_chunks_flagged"]}/{detail["good_chunks_total"]}</small></td><td style="{good(caught)}">{caught:.0%}<small>{detail["wrong_flagged"]}/{detail["wrong_total"]}</small></td></tr>'

STYLE = """
:root{--bg:#0B0E13;--line:#252C37;--ink:#F4F6F9;--muted:#A8B1BF;--accent:#46E0B5}
*{box-sizing:border-box;margin:0}
body{width:1600px;height:900px;background:var(--bg);color:var(--ink);font-family:-apple-system,"SF Pro Display","Helvetica Neue",Arial,sans-serif;padding:38px 52px 26px;display:flex;flex-direction:column}
.eyebrow{color:var(--accent);font-size:19px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}
h1{font-size:44px;line-height:1.05;font-weight:750;letter-spacing:-.025em;margin-top:8px}
.sub{font-size:22px;color:var(--muted);margin-top:10px}
table{width:100%;border-collapse:separate;border-spacing:4px;table-layout:fixed;margin-top:20px;flex:1}
thead th{font-size:18px;font-weight:650;color:var(--ink);line-height:1.2;height:64px;vertical-align:bottom;padding:0 8px 6px}
thead th:first-child{width:300px}
tbody th{text-align:left;font-size:22px;font-weight:650}
td{height:60px;text-align:center;font-size:29px;font-weight:750;border-radius:7px;font-variant-numeric:tabular-nums;position:relative}
small{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:15px;font-weight:600;opacity:.8}
footer{display:flex;justify-content:space-between;gap:36px;align-items:flex-end;margin-top:12px;font-size:16.5px;color:var(--muted);line-height:1.3}
.repo{color:var(--ink);font-weight:650;white-space:nowrap;font-size:20px}
"""
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>RAG Eval Suite V2</title><style>{STYLE}</style></head><body>
<div class="eyebrow">RAG Eval Suite · Real answers</div>
<h1>Cheap metrics flagged 27–65% of good real answers. An LLM judge flagged 2%.</h1>
<div class="sub">Same frozen thresholds as the planted test. Part of the gap is that gold-based paraphrases sit closer to gold than real answers do.</div>
<table><thead><tr><th>Does it match the correct answer?</th><th>Planted paraphrased or longer answers flagged</th><th>Good real answers flagged</th><th>Wrong or partial real answers caught, excluding refusals</th></tr></thead><tbody>{body}</tbody></table>
<footer><div>Real answers from glm-5.3-flash on IRS test questions, labeled by AI agents without seeing scores, no human review. Good answers came from retrieved chunks, and wrong ones from chunks or evidence-removed context. Small samples, and answers from one generator.</div><div class="repo">github.com/fixverified/rag-eval-suite</div></footer>
</body></html>"""
Path("docs/results_v2.html").write_text(html)
