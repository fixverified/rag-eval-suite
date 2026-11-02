"""Build docs/results.html from results/v1/summary.json."""

import json
from pathlib import Path

SUMMARY = json.loads(Path("results/v1/summary.json").read_text())
S = {**SUMMARY["frozen"], "ragas_at_0_5": SUMMARY["library_at_0_5"]["ragas.faithfulness@gpt-6-luna"]}
J = "@gpt-6-luna"
FAITHFUL = [("LLM judge", f"faithfulness_llm{J}"), ("Ragas, calibrated", f"ragas.faithfulness{J}"), ("Ragas, threshold 0.5", "ragas_at_0_5"), ("DeepEval", f"deepeval.faithfulness{J}"), ("LettuceDetect", "lettucedetect"), ("Sentence NLI", "sentence_nli"), ("Number grounding", "number_grounding"), ("Token overlap", "token_support")]
FAITHFUL_COLS = [("Wrong number", "wrong_number"), ("Negation", "negation"), ("Wrong condition", "wrong_condition"), ("Made-up detail", "unsupported_addition"), ("Answered without evidence", "wrongful_answer")]
CORRECT = [("LLM judge", f"correctness_llm{J}"), ("Ragas correctness", f"ragas.answer_correctness{J}"), ("NLI", "nli_correctness"), ("Exact facts", "exact_facts"), ("Embedding similarity", "embedding_similarity"), ("Token F1", "token_f1"), ("BLEU", "bleu")]
CORRECT_COLS = [("Wrong number", "wrong_number"), ("Negation", "negation"), ("Wrong condition", "wrong_condition"), ("Off-topic", "off_topic"), ("Wrong refusal", "wrongful_refusal")]


def shade(value: float) -> str:
    return f"rgba(70,224,181,{0.08 + 0.80 * value:.2f})"


def panel(title: str, rows: list, columns: list) -> str:
    head = "".join(f"<th>{name}</th>" for name, _ in columns)
    body = ""
    for name, key in rows:
        entry = S[key]
        cells = ""
        if entry["threshold"] == 0:
            body += f'<tr><th class="name">{name}</th><td class="none" colspan="{len(columns)}">No threshold above 0 held false alarms to 5% on dev (AUROC {entry["auroc"]:.2f})</td><td class="fa">–</td></tr>'
            continue
        for _, category in columns:
            item = entry["categories"].get(category)
            if item is None:
                cells += '<td class="na">–</td>'
            else:
                mark = "*" if item["questions"] < 30 else ""
                ink = "#07130F" if item["recall"] >= 0.55 else "#F4F6F9"
                cells += f'<td style="background:{shade(item["recall"])};color:{ink}">{item["recall"]:.0%}{mark}</td>'
        body += f'<tr><th class="name">{name}</th>{cells}<td class="fa">{entry["fpr"]:.0%}</td></tr>'
    return f'<section><h2>{title}</h2><table><thead><tr><th></th>{head}<th class="fah">False alarms</th></tr></thead><tbody>{body}</tbody></table></section>'


STYLE = """
:root{--bg:#0B0E13;--line:#252C37;--ink:#F4F6F9;--muted:#A8B1BF;--accent:#46E0B5}
*{box-sizing:border-box;margin:0}
body{width:1600px;height:900px;background:var(--bg);color:var(--ink);font-family:-apple-system,"SF Pro Display","Helvetica Neue",Arial,sans-serif;padding:38px 52px 26px;display:flex;flex-direction:column}
.eyebrow{color:var(--accent);font-size:19px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}
h1{font-size:52px;line-height:1.05;font-weight:750;letter-spacing:-.025em;margin-top:8px}
.sub{font-size:22px;color:var(--muted);margin-top:10px}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:34px;margin-top:22px;flex:1}
h2{font-size:25px;font-weight:700;margin-bottom:10px}
table{width:100%;border-collapse:separate;border-spacing:3px;table-layout:fixed}
thead th{font-size:14.5px;font-weight:600;color:var(--muted);line-height:1.15;height:62px;vertical-align:bottom;padding:0 2px 5px}
th.name{text-align:left;font-size:17px;font-weight:600;width:178px;white-space:nowrap}
thead th:first-child{width:178px}
td{height:56px;text-align:center;font-size:22px;font-weight:750;border-radius:6px;font-variant-numeric:tabular-nums}
td.na{color:#667}
td.none{font-size:17px;font-weight:600;color:var(--muted);background:#141922}
td.fa{background:transparent;border:1px solid var(--line);font-weight:600;color:var(--ink)}
.fah{color:var(--ink)!important}
footer{display:flex;justify-content:space-between;gap:36px;align-items:flex-end;margin-top:12px;font-size:16.5px;color:var(--muted);line-height:1.3}
.repo{color:var(--ink);font-weight:650;white-space:nowrap;font-size:20px}
"""

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>RAG Eval Suite</title><style>{STYLE}</style></head><body>
<div class="eyebrow">RAG Eval Suite</div>
<h1>Same bad answers. Very different catch rates.</h1>
<div class="sub">Share of planted failures each evaluator flagged, at thresholds frozen on separate data before a one-time test.</div>
<div class="panels">{panel("Is the answer supported by its sources?", FAITHFUL, FAITHFUL_COLS)}{panel("Does it match the correct answer?", CORRECT, CORRECT_COLS)}</div>
<footer><div>50 sealed test questions on IRS publications, 20–30 per failure shown. Planted failures are often easier than real ones. Our LLM prompts were tuned on dev, and library prompts are as shipped. DeepEval checks for contradiction, so unsupported claims often pass by design. All LLM evaluators use gpt-6-luna. * under 30 questions.</div><div class="repo">github.com/fixverified/rag-eval-suite</div></footer>
</body></html>"""
Path("docs/results.html").write_text(html)
