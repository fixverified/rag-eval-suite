# Version 2 results

Real answers from `z-ai/glm-5.3-flash` on all 100 test questions, added after version 1 was public. Version 1 thresholds and prompts are unchanged. Two AI agents labeled answers without seeing scores, and a third settled their 5 disagreements out of about 1,000 labels. No human has reviewed these labels.

Ragas and DeepEval ran only on chunk and evidence-removed answers, so they have fewer rows than other evaluators in the table below. Answers are reused across modes, so these counts aren't independent questions. Ranges are 95% Wilson intervals at answer level, which makes them too narrow where answers cluster by question.

## Results on questions unused in version 1

These 30 answerable and 20 unanswerable questions weren't in version 1's cases, so they're a cleaner check, though the same thresholds and judge apply.

| Evaluator | Real failures flagged | Real good answers flagged |
|---|---:|---:|
| `abstention_llm` | 2/6 | 1/73 |
| `abstention_reranker` | 2/6 | 24/73 |
| `abstention_rule` | 2/6 | 24/73 |
| `bleu` | 34/45 | 38/66 |
| `completeness_llm` | 40/42 | 0/69 |
| `correctness_llm` | 43/45 | 2/66 |
| `cross_encoder_relevance` | 0/0 | 0/96 |
| `deepeval.answer_relevancy` | 0/0 | 0/45 |
| `deepeval.faithfulness` | 0/4 | 0/40 |
| `embedding_relevance` | 0/0 | 1/96 |
| `embedding_similarity` | 32/45 | 38/66 |
| `exact_facts` | 29/45 | 29/66 |
| `faithfulness_llm` | 3/5 | 1/40 |
| `key_point_mean` | 17/42 | 1/69 |
| `lettucedetect` | 0/5 | 1/40 |
| `nli_correctness` | 22/45 | 13/66 |
| `number_grounding` | 0/5 | 5/40 |
| `ragas.answer_correctness` | 30/30 | 11/29 |
| `ragas.answer_relevancy` | 0/0 | 3/45 |
| `relevance_llm` | 0/0 | 11/96 |
| `rouge_l` | 36/45 | 43/66 |
| `sentence_nli` | 1/5 | 2/40 |
| `token_f1` | 38/45 | 51/66 |
| `token_support` | 1/5 | 3/40 |

## How the generator did

| Mode | Answerable answers correct | Answers unsupported by their context |
|---|---:|---:|
| closed book | 41/59 | – |
| chunks | 48/60 | 2 |
| gold removed | 19/59 | 4 |
| full document | 49/52 | 1 |

With retrieved chunks, it handled 40 of 40 unanswerable questions correctly.

## Evaluators on real answers

| Evaluator | Dimension | Threshold | Real failures flagged | Real good answers flagged | Errors |
|---|---|---:|---:|---:|---:|
| `abstention_llm` | abstention | 1.0000 | 4/8 (50%, 22%–78%) | 2/151 (1%, 0%–5%) | 0 |
| `abstention_reranker` | abstention | 0.1554 | 3/8 (38%, 14%–69%) | 45/151 (30%, 23%–38%) | 0 |
| `abstention_rule` | abstention | 1.0000 | 2/8 (25%, 7%–59%) | 45/151 (30%, 23%–38%) | 0 |
| `completeness_llm` | complete | 1.0000 | 69/71 (97%, 90%–99%) | 0/159 (0%, 0%–2%) | 0 |
| `key_point_mean` | complete | 0.0682 | 36/71 (51%, 39%–62%) | 2/159 (1%, 0%–4%) | 0 |
| `key_point_nli` | complete | 0.0000 | no threshold | no threshold | 0 |
| `bleu` | correct | 0.1915 | 60/73 (82%, 72%–89%) | 80/157 (51%, 43%–59%) | 0 |
| `correctness_llm` | correct | 1.0000 | 71/73 (97%, 91%–99%) | 6/157 (4%, 2%–8%) | 0 |
| `embedding_similarity` | correct | 0.8711 | 59/73 (81%, 70%–88%) | 114/157 (73%, 65%–79%) | 0 |
| `exact_facts` | correct | 0.5000 | 49/73 (67%, 56%–77%) | 47/157 (30%, 23%–38%) | 0 |
| `nli_correctness` | correct | 0.0035 | 41/73 (56%, 45%–67%) | 49/157 (31%, 24%–39%) | 0 |
| `ragas.answer_correctness` | correct | 0.7891 | 52/52 (100%, 93%–100%) | 27/67 (40%, 29%–52%) | 0 |
| `rouge_l` | correct | 0.4231 | 64/73 (88%, 78%–93%) | 92/157 (59%, 51%–66%) | 0 |
| `token_f1` | correct | 0.5333 | 66/73 (90%, 82%–95%) | 109/157 (69%, 62%–76%) | 0 |
| `deepeval.faithfulness` | faithful | 0.5000 | 0/5 (0%, 0%–43%) | 2/79 (3%, 1%–9%) | 5 |
| `faithfulness_llm` | faithful | 0.7500 | 4/6 (67%, 30%–90%) | 1/80 (1%, 0%–7%) | 0 |
| `lettucedetect` | faithful | 0.6316 | 0/6 (0%, 0%–39%) | 2/80 (2%, 1%–9%) | 0 |
| `number_grounding` | faithful | 0.5000 | 1/6 (17%, 3%–56%) | 5/80 (6%, 3%–14%) | 0 |
| `ragas.faithfulness` | faithful | 0.0000 | no threshold | no threshold | 0 |
| `sentence_nli` | faithful | 0.0613 | 1/6 (17%, 3%–56%) | 4/80 (5%, 2%–12%) | 0 |
| `token_support` | faithful | 0.6000 | 2/6 (33%, 10%–70%) | 3/80 (4%, 1%–10%) | 0 |
| `cross_encoder_relevance` | relevant | 0.0019 | 0/1 (0%, 0%–79%) | 0/194 (0%, 0%–2%) | 0 |
| `deepeval.answer_relevancy` | relevant | 1.0000 | 1/1 (100%, 21%–100%) | 0/85 (0%, 0%–4%) | 0 |
| `embedding_relevance` | relevant | 0.6452 | 0/1 (0%, 0%–79%) | 1/194 (1%, 0%–3%) | 0 |
| `ragas.answer_relevancy` | relevant | 0.6386 | 0/1 (0%, 0%–79%) | 3/85 (4%, 1%–10%) | 0 |
| `relevance_llm` | relevant | 1.0000 | 1/1 (100%, 21%–100%) | 12/194 (6%, 4%–10%) | 0 |

## Correctness: refusals vs. wrong answers

Most real failures here are refusals, which any similarity metric catches. This table separates them, using only answers from chunks or evidence-removed context, which every evaluator saw. Wrong answers include partial ones, mostly correct answers that declined part of a question.

| Evaluator | Wrong or partial non-refusals flagged | Refusals on answerable questions flagged | Good chunk answers flagged |
|---|---:|---:|---:|
| `bleu` | 11/19 | 34/35 | 20/48 |
| `correctness_llm` | 19/19 | 35/35 | 1/48 |
| `embedding_similarity` | 9/19 | 34/35 | 31/48 |
| `exact_facts` | 8/19 | 27/35 | 13/48 |
| `nli_correctness` | 10/19 | 20/35 | 20/48 |
| `ragas.answer_correctness` | 19/19 | 33/33 | 18/48 |
| `rouge_l` | 13/19 | 35/35 | 20/48 |
| `token_f1` | 15/19 | 35/35 | 28/48 |

## Chunks vs. full document

Each cell scores answers with `faithfulness_llm`. Flagged means below the frozen threshold.

| Generated from | Judged against | Questions | Mean score | Flagged | Errors |
|---|---|---:|---:|---:|---:|
| chunks | chunks | 52 | 0.97 | 2 | 0 |
| chunks | document | 52 | 0.85 | 9 | 0 |
| document | chunks | 52 | 0.81 | 11 | 0 |
| document | document | 52 | 0.93 | 3 | 0 |

On the same 52 single-publication questions, chunks produced 43 correct answers and the full publication 49. The document was right and chunks wrong on 8 questions, 5 of them chunk refusals. The reverse happened on 2. Refusals count in these cells, and `faithfulness_llm` isn't designed to score them, so the chunks-judged-against-document cell mixes refusals with real unsupported claims.

Answers flagged against chunks but not against the document: 0 generated from chunks, 8 generated from the document.
