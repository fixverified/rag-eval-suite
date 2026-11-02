"""Build docs/overview.html, one page covering versions 1 to 3."""

import json
from pathlib import Path

V1 = json.loads(Path("results/v1/summary.json").read_text())["frozen"]
V2 = json.loads(Path("results/v2/summary.json").read_text())
V3 = json.loads(Path("results/v3/summary.json").read_text())
J = "@gpt-6-luna"
ROWS = [("LLM judge", "correctness_llm"), ("Ragas correctness", "ragas.answer_correctness"), ("Exact facts", "exact_facts"), ("NLI", "nli_correctness"), ("Token F1", "token_f1"), ("ROUGE-L", "rouge_l"), ("BLEU", "bleu"), ("Embedding similarity", "embedding_similarity")]
LLM_BASED = {"correctness_llm", "ragas.answer_correctness"}


def key(name: str) -> str:
    return f"{name}{J}" if name in LLM_BASED else name


def good(value: float) -> str:
    return f"background:rgba(70,224,181,{0.08 + 0.80 * value:.2f});color:{'#07130F' if value >= 0.55 else '#F4F6F9'}"


def bad(value: float) -> str:
    return f"background:rgba(255,155,84,{0.08 + 0.85 * value:.2f});color:{'#1B0E05' if value >= 0.55 else '#F4F6F9'}"


body = ""
for label, name in ROWS:
    planted = V1[key(name)]["categories"]["wrong_number"]["recall"]
    detail = V2["correctness_detail"][key(name)]
    flagged = detail["good_chunks_flagged"] / detail["good_chunks_total"]
    caught = detail["wrong_flagged"] / detail["wrong_total"]
    area = V3["calibration"][name]["auroc_wrong_vs_good"]
    body += f'<tr><th>{label}</th><td style="{good(planted)}">{planted:.0%}</td><td style="{bad(flagged)}">{flagged:.0%}</td><td style="{good(caught)}">{caught:.0%}</td><td style="{good(max(area - 0.5, 0) * 2)}">{area:.2f}</td></tr>'

paired = V2["paired_chunks_vs_document"]
closed = next(g for g in V2["generator"] if g["mode"] == "closed_book")
stability = V3["repeats"]["correctness_llm"]
faithful_stability = V3["repeats"]["faithfulness_llm"]
tiles = [
    (f"{paired['document_correct']} vs. {paired['chunks_correct']}", f"correct on the same {paired['questions']} questions, full publication vs. chunks. Not significant, and full document was handed the right publication."),
    (f"{closed['answerable_correct']} of {closed['answerable_total']}", "correct with no retrieval, so a right answer doesn't prove retrieval worked."),
    (f"{stability['verdict_changed']} of {stability['answers']}", f"correctness verdicts changed across 5 runs. Faithfulness changed on {faithful_stability['verdict_changed']} of {faithful_stability['answers']}."),
    ("15 of 20", "clean refusals wrongly flagged by a refusal rule on sealed test, after 1 of 400 clean answers on dev."),
]
tile_html = "".join(f'<div class="tile"><b>{big}</b><span>{small}</span></div>' for big, small in tiles)

STYLE = """
:root{--bg:#0B0E13;--line:#252C37;--ink:#F4F6F9;--muted:#A8B1BF;--accent:#46E0B5}
*{box-sizing:border-box;margin:0}
body{width:1600px;height:900px;background:var(--bg);color:var(--ink);font-family:-apple-system,"SF Pro Display","Helvetica Neue",Arial,sans-serif;padding:36px 50px 24px;display:flex;flex-direction:column}
.eyebrow{color:var(--accent);font-size:19px;font-weight:700;letter-spacing:.09em;text-transform:uppercase}
h1{font-size:50px;line-height:1.05;font-weight:750;letter-spacing:-.025em;margin-top:8px}
.sub{font-size:22px;color:var(--muted);margin-top:9px}
.layout{display:grid;grid-template-columns:1fr 390px;gap:30px;margin-top:18px;flex:1;min-height:0}
table{width:100%;height:100%;border-collapse:separate;border-spacing:4px;table-layout:fixed}
thead th{font-size:16.5px;font-weight:650;line-height:1.18;height:72px;vertical-align:bottom;padding:0 7px 7px}
thead small{display:block;color:var(--accent);font-size:13.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;margin-bottom:4px}
thead th:first-child{width:215px}
tbody th{text-align:left;font-size:20px;font-weight:650}
td{text-align:center;font-size:29px;font-weight:750;border-radius:7px;font-variant-numeric:tabular-nums}
.tiles{display:grid;grid-template-rows:repeat(4,1fr);gap:12px}
.tile{border:1px solid var(--line);border-radius:12px;padding:13px 18px;display:flex;flex-direction:column;justify-content:center;background:#121720}
.tile b{font-size:34px;font-weight:750;letter-spacing:-.01em}
.tile span{font-size:15.5px;line-height:1.28;color:var(--muted);margin-top:5px}
footer{display:flex;justify-content:space-between;gap:34px;align-items:flex-end;margin-top:13px;font-size:15.5px;color:var(--muted);line-height:1.3}
.repo{color:var(--ink);font-weight:650;white-space:nowrap;font-size:20px}
"""
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>RAG Eval Suite</title><style>{STYLE}</style></head><body>
<div class="eyebrow">RAG Eval Suite · Overview</div>
<h1>Can you trust a RAG correctness score? It depends on the evaluator.</h1>
<div class="sub">Eight evaluators, tested on planted failures and real answers, at thresholds frozen before testing.</div>
<div class="layout"><table><thead><tr><th></th><th><small>Planted</small>Wrong numbers caught</th><th><small>Real</small>Good answers wrongly flagged</th><th><small>Real</small>Wrong or partial answers caught</th><th><small>Real</small>Separates wrong from good (AUROC)</th></tr></thead><tbody>{body}</tbody></table><div class="tiles">{tile_html}</div></div>
<footer><div>IRS publications. Planted: 28 sealed questions. Real: 48 good and 19 wrong or partial answers from glm-5.3-flash, excluding refusals, with AUROC on 67 good answers. Small samples, one corpus, and AI-written labels with no human review. Our LLM prompts were tuned on dev, and Ragas used shipped prompts.</div><div class="repo">github.com/fixverified/rag-eval-suite</div></footer>
</body></html>"""
Path("docs/overview.html").write_text(html)
