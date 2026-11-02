from rag_eval_suite.corpus import build_chunks, chunk_page, clean_page, normalize, quote_on_page


def test_clean_page_repairs_kerning_and_line_hyphens():
    assert clean_page("T able 1. Y ou may re-\nsponsibility") == "Table 1. You may responsibility"


def test_clean_page_keeps_real_one_letter_words():
    assert clean_page("A way and I am") == "A way and I am"


def test_normalize_handles_quotes_case_and_hyphens():
    assert normalize("Don’t  Self-\nEmployed") == normalize("don't selfemployed")


def test_chunks_overlap_and_keep_every_sentence():
    page = {"publication": "x", "page": 1, "text": " ".join(f"Sentence number {i} has six words." for i in range(100))}
    chunks = chunk_page(page, chunk_words=60, overlap_words=12)
    assert len(chunks) > 1
    assert all(f"number {i} has" in " ".join(c.text for c in chunks) for i in range(100))
    assert chunks[0].text.split(". ")[-1].rstrip(".") in chunks[1].text


def test_chunk_ids_are_unique_across_corpus():
    chunks = build_chunks()
    assert len({c.id for c in chunks}) == len(chunks)
    assert {c.publication for c in chunks} == {"501", "502", "503", "523", "590a", "590b", "596", "936", "969", "970"}


def test_real_quote_is_found_on_its_page_only():
    quote = "Y ou may be held jointly and individually responsible".replace("Y ou", "You")
    assert quote_on_page(quote, "501", 7)
    assert not quote_on_page(quote, "501", 8)
