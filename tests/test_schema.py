import pytest

from rag_eval_suite.schema import ALL_LABELS, DIMENSIONS, EXPLOITS, SPLITS, numbers_in, validate_case, validate_question

GOOD = {
    "id": "q1",
    "question": "What can make you jointly responsible?",
    "answerable": True,
    "type": "single_fact",
    "gold_answer": "You may be held jointly and individually responsible.",
    "key_points": ["jointly and individually responsible"],
    "evidence": [{"publication": "501", "page": 7, "quote": "You may be held jointly and individually responsible"}],
}


def test_splits_share_no_publication():
    names = list(SPLITS.values())
    assert sum(map(len, names)) == len(set().union(*names)) == 10


@pytest.mark.parametrize("name", ALL_LABELS)
def test_every_label_covers_every_dimension(name):
    assert set(ALL_LABELS[name]) == set(DIMENSIONS)


def test_good_question_passes():
    assert validate_question(GOOD, "dev") == []


def test_fabricated_quote_fails():
    bad = {**GOOD, "evidence": [{"publication": "501", "page": 7, "quote": "You must always file jointly every single year"}]}
    assert "not on 501" in validate_question(bad, "dev")[0]


def test_evidence_from_another_split_fails():
    bad = {**GOOD, "evidence": [{"publication": "970", "page": 1, "quote": "a quote long enough to be checked here"}]}
    assert "outside split" in validate_question(bad, "dev")[0]


def test_wrong_number_must_change_a_number():
    question = {**GOOD, "gold_answer": "The limit is $4,300."}
    case = {"case_id": "c", "question_id": "q1", "category": "wrong_number", "origin": "injected", "answer": "The limit is $4,300."}
    assert validate_case(case, question, "dev") == ["wrong_number didn't change a number"]
    assert validate_case({**case, "answer": "The limit is $4,500."}, question, "dev") == []


def test_held_out_exploit_rejected_in_dev():
    case = {"case_id": "c", "question_id": "q1", "category": "copied_source", "origin": "injected", "answer": "x"}
    assert validate_case(case, GOOD, "dev") == ["copied_source is held out of dev"]


def test_numbers_in_normalizes_commas():
    assert numbers_in("From $4,300 to 8,550.") == {"4300", "8550"}
    assert EXPLOITS
