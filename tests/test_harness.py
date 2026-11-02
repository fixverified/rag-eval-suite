import json

from rag_eval_suite.harness import _evaluators, run_cases
from rag_eval_suite.schema import ALL_LABELS

QUESTION = {"id": "q", "question": "What is the limit?", "answerable": True, "gold_answer": "The limit is $4,300.", "key_points": ["limit is $4,300"]}
UNANSWERABLE = {"id": "u", "question": "What is the state rule?", "answerable": False}
CONTEXTS = {
    "q": {"with_gold": [{"id": "a", "text": "The limit is $4,300."}], "without_gold": [{"id": "b", "text": "Cats climb trees."}]},
    "u": {"without_gold": [{"id": "b", "text": "Cats climb trees."}]},
}
BAD = {"case_id": "c1", "question_id": "q", "category": "wrong_number", "origin": "injected", "answer": "The limit is $9,000."}


def run(tmp_path, cases, llm=None, kinds=None, only=None):
    out = tmp_path / "scores.jsonl"
    run_cases(cases, {"q": QUESTION, "u": UNANSWERABLE}, CONTEXTS, ALL_LABELS, out, llm=llm, judge="j" if llm else None, kinds=kinds, only=only)
    return [json.loads(line) for line in out.read_text().splitlines()]


def test_heuristics_score_a_wrong_number_with_correct_label(tmp_path):
    rows = {r["evaluator"]: r for r in run(tmp_path, [BAD], kinds={"heuristic"})}
    assert rows["number_grounding"]["score"] == 0
    assert rows["number_grounding"]["label_good"] is False
    assert rows["exact_facts"]["score"] == 0
    assert "citations_exist" not in rows


def test_gold_evaluators_are_na_on_unanswerable_questions(tmp_path):
    case = {"case_id": "c2", "question_id": "u", "category": "wrongful_answer", "origin": "injected", "answer": "The state rule is 5."}
    rows = {r["evaluator"]: r for r in run(tmp_path, [case], kinds={"heuristic"})}
    assert "exact_facts" not in rows
    assert rows["abstention_rule"]["score"] == 0


def test_undefined_dimension_is_never_scored(tmp_path):
    case = {**BAD, "case_id": "c3", "category": "off_topic", "answer": "Something else."}
    assert all(r["dimension"] != "faithful" for r in run(tmp_path, [case], kinds={"heuristic"}))


def test_judge_failures_are_errors_not_scores(tmp_path):
    rows = run(tmp_path, [BAD], llm=lambda prompt: "nonsense", kinds={"llm"}, only={"faithfulness_llm"})
    assert rows[0]["score"] is None
    assert rows[0]["error"].startswith("JudgeError")


def test_rerun_skips_finished_rows(tmp_path):
    assert len(run(tmp_path, [BAD], kinds={"heuristic"})) == len(run(tmp_path, [BAD], kinds={"heuristic"}))


def test_all_evaluators_have_valid_dimensions():
    assert all(e.dimension in next(iter(ALL_LABELS.values())) for e in _evaluators(lambda p: ""))
