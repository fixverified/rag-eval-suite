# Results

Version 1. All figures come from the sealed test set, run once with thresholds, prompts and versions frozen on dev. Recall is the share of known-bad answers flagged. False alarms are clean controls wrongly flagged. Both are at question level.

Most categories have 30 questions, and some have 14–29. With 30, a perfect 100% still has a 95% lower bound near 89%, and 0% false alarms an upper bound near 11%. A `*` marks fewer than 30 questions, which is exploratory. A `–` means that evaluator wasn't scored on that failure, by the [scope table](SCOPE.md). `no threshold` means holding false alarms to 5% on dev required a threshold of 0, so the evaluator can flag nothing there, though its AUROC below may still be high. Context evaluators are compared on the 30 answerable questions.

Every case is injected, and clean controls derive from gold answers. False alarms therefore say nothing about real model answers. Test cases were written by a separate agent and kept out of dev work, but the builder and assistant knew the failure categories and exploit families, so this isn't full blinding.

## Failures

| Evaluator | Dimension | False alarms | wrong number | negation | wrong condition | unsupported addition | unsupported true | wrongful answer | off topic | incomplete | wrongful refusal | bad citation | context missing |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `deepeval.faithfulness` | faithful | 5% | 75%* | 79%* | 53% | 0% | 12%* | 0%* | – | – | – | – | – |
| `faithfulness_llm` | faithful | 0% | 100%* | 100% | 100% | 83% | 100%* | 100%* | – | – | – | – | – |
| `lettucedetect` | faithful | 4% | 32%* | 3% | 13% | 37% | 67%* | 60%* | – | – | – | – | – |
| `number_grounding` | faithful | 1% | 57%* | 0% | 3% | 0% | 72%* | 45%* | – | – | – | – | – |
| `ragas.faithfulness` | faithful | 0% | no threshold | no threshold | no threshold | no threshold | no threshold | no threshold | – | – | – | – | – |
| `sentence_nli` | faithful | 2% | 21%* | 23% | 27% | 20% | 28%* | 25%* | – | – | – | – | – |
| `token_support` | faithful | 1% | 0%* | 13% | 0% | 23% | 39%* | 35%* | – | – | – | – | – |
| `bleu` | correct | 9% | 0%* | 17% | 0% | – | – | – | 100% | – | 100% | – | – |
| `correctness_llm` | correct | 0% | 100%* | 100% | 100% | – | – | – | 100% | – | 100% | – | – |
| `embedding_similarity` | correct | 14% | 4%* | 50% | 10% | – | – | – | 100% | – | 100% | – | – |
| `exact_facts` | correct | 9% | 61%* | 10% | 0% | – | – | – | 93% | – | 93% | – | – |
| `nli_correctness` | correct | 7% | 61%* | 87% | 67% | – | – | – | 70% | – | 80% | – | – |
| `ragas.answer_correctness` | correct | 11% | 96%* | 93% | 87% | – | – | – | 100% | – | 100% | – | – |
| `rouge_l` | correct | 17% | 0%* | 17% | 0% | – | – | – | 100% | – | 100% | – | – |
| `token_f1` | correct | 11% | 0%* | 27% | 0% | – | – | – | 100% | – | 100% | – | – |
| `cross_encoder_relevance` | relevant | 5% | – | – | – | – | – | – | 77% | – | – | – | – |
| `deepeval.answer_relevancy` | relevant | 2% | – | – | – | – | – | – | 100% | – | – | – | – |
| `embedding_relevance` | relevant | 7% | – | – | – | – | – | – | 97% | – | – | – | – |
| `ragas.answer_relevancy` | relevant | 4% | – | – | – | – | – | – | 87% | – | – | – | – |
| `relevance_llm` | relevant | 0% | – | – | – | – | – | – | 97% | – | – | – | – |
| `completeness_llm` | complete | 0% | – | – | – | – | – | – | 100% | 93%* | 100% | – | – |
| `key_point_mean` | complete | 1% | – | – | – | – | – | – | 93% | 0%* | 100% | – | – |
| `key_point_nli` | complete | 0% | – | – | – | – | – | – | no threshold | no threshold | no threshold | – | – |
| `abstention_llm` | abstention | 0% | – | – | – | – | – | 100%* | – | – | 100% | – | – |
| `abstention_reranker` | abstention | 10% | – | – | – | – | – | 25%* | – | – | 33% | – | – |
| `abstention_rule` | abstention | 30% | – | – | – | – | – | 100%* | – | – | 33% | – | – |
| `citation_coverage` | citation | 0% | – | – | – | – | – | – | – | – | – | 0% | – |
| `citation_support` | citation | 0% | – | – | – | – | – | – | – | – | – | no threshold | – |
| `citations_exist` | citation | 0% | – | – | – | – | – | – | – | – | – | 63% | – |
| `context_relevance_reranker` | context | 3% | – | – | – | – | – | – | – | – | – | – | 20% |
| `context_sufficiency_llm` | context | 0% | – | – | – | – | – | – | – | – | – | – | 67% |
| `deepeval.contextual_recall` | context | 1% | – | – | – | – | – | – | – | – | – | – | 61% |
| `ragas.context_recall` | context | 0% | – | – | – | – | – | – | – | – | – | – | 64% |
| `signal_ratio` | context | 3% | – | – | – | – | – | – | – | – | – | – | 17% |

## Exploits

Copied source, confident tone, number format and context number were held out of dev entirely.

| Evaluator | Dimension | False alarms | query stuffing | padding | prompt injection | copied source | confident tone | number format | context number |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `deepeval.faithfulness` | faithful | 5% | 0%* | 3% | 50% | – | 90%* | 70%* | 62%* |
| `faithfulness_llm` | faithful | 0% | 100% | 100% | 100% | – | 100% | 100%* | 100%* |
| `lettucedetect` | faithful | 4% | 0% | 60% | 63% | – | 50% | 46%* | 8%* |
| `number_grounding` | faithful | 1% | 0% | 53% | 10% | – | 47% | 39%* | 0%* |
| `ragas.faithfulness` | faithful | 0% | no threshold | no threshold | no threshold | – | no threshold | no threshold | no threshold |
| `sentence_nli` | faithful | 2% | 7% | 80% | 33% | – | 30% | 7%* | 8%* |
| `token_support` | faithful | 1% | 43% | 100% | 73% | – | 53% | 4%* | 0%* |
| `bleu` | correct | 9% | 100% | 77% | 20% | 100% | 60% | 0%* | 0%* |
| `correctness_llm` | correct | 0% | 100% | 100% | 100% | 100% | 100% | 100%* | 100%* |
| `embedding_similarity` | correct | 14% | 97% | 87% | 63% | 100% | 83% | 11%* | 27%* |
| `exact_facts` | correct | 9% | 93% | 67% | 20% | 93% | 63% | 57%* | 62%* |
| `nli_correctness` | correct | 7% | 57% | 93% | 80% | 67% | 70% | 29%* | 100%* |
| `ragas.answer_correctness` | correct | 11% | 100% | 100% | 90% | 100% | 100% | 96%* | 100%* |
| `rouge_l` | correct | 17% | 97% | 93% | 23% | 100% | 63% | 0%* | 0%* |
| `token_f1` | correct | 11% | 100% | 100% | 40% | 100% | 67% | 0%* | 0%* |
| `cross_encoder_relevance` | relevant | 5% | 0% | – | – | 20% | – | – | – |
| `deepeval.answer_relevancy` | relevant | 2% | 43% | – | – | 71%* | – | – | – |
| `embedding_relevance` | relevant | 7% | 10% | – | – | 20% | – | – | – |
| `ragas.answer_relevancy` | relevant | 4% | 90% | – | – | 20% | – | – | – |
| `relevance_llm` | relevant | 0% | 100% | – | – | 100% | – | – | – |
| `completeness_llm` | complete | 0% | 100% | – | – | 100% | – | – | – |
| `key_point_mean` | complete | 1% | 100% | – | – | 100% | – | – | – |
| `key_point_nli` | complete | 0% | no threshold | – | – | no threshold | – | – | – |
| `abstention_llm` | abstention | 0% | – | – | – | – | – | – | – |
| `abstention_reranker` | abstention | 10% | – | – | – | – | – | – | – |
| `abstention_rule` | abstention | 30% | – | – | – | – | – | – | – |
| `citation_coverage` | citation | 0% | – | – | – | – | – | – | – |
| `citation_support` | citation | 0% | – | – | – | – | – | – | – |
| `citations_exist` | citation | 0% | – | – | – | – | – | – | – |
| `context_relevance_reranker` | context | 3% | – | – | – | – | – | – | – |
| `context_sufficiency_llm` | context | 0% | – | – | – | – | – | – | – |
| `deepeval.contextual_recall` | context | 1% | – | – | – | – | – | – | – |
| `ragas.context_recall` | context | 0% | – | – | – | – | – | – | – |
| `signal_ratio` | context | 3% | – | – | – | – | – | – | – |

## Ranking quality and reliability

| Evaluator | Threshold | AUROC | AUPRC | False alarms, 95% interval | Errors | Median seconds |
|---|---:|---:|---:|---:|---:|---:|
| `abstention_llm` | 1.00 | 1.00 | 1.00 | 0%–7% | 0/646 | 1.83 |
| `abstention_reranker` | 0.16 | 0.74 | 0.50 | 4%–21% | 0/646 | 0.04 |
| `abstention_rule` | 1.00 | 0.76 | 0.48 | 19%–44% | 0/646 | 0.00 |
| `bleu` | 0.19 | 0.72 | 0.74 | 3%–25% | 0/580 | 0.00 |
| `citation_coverage` | 0.33 | 0.50 | 0.50 | 0%–11% | 0/60 | 0.00 |
| `citation_support` | 0.00 | 0.99 | 0.99 | 0%–11% | 0/60 | 0.09 |
| `citations_exist` | 1.00 | 0.82 | 0.82 | 0%–11% | 0/60 | 0.00 |
| `completeness_llm` | 1.00 | 0.99 | 0.99 | 0%–11% | 0/392 | 1.33 |
| `context_relevance_reranker` | 0.70 | 0.71 | 0.61 | 1%–17% | 0/150 |  |
| `context_sufficiency_llm` | 1.00 | 0.82 | 0.77 | 0%–11% | 0/150 |  |
| `correctness_llm` | 1.00 | 1.00 | 1.00 | 0%–11% | 0/580 | 1.37 |
| `cross_encoder_relevance` | 0.00 | 0.97 | 0.82 | 1%–19% | 0/594 | 0.01 |
| `deepeval.answer_relevancy` | 1.00 | 1.00 | 1.00 | 0%–15% | 6/594 | 3.48 |
| `deepeval.contextual_recall` | 0.50 | 0.78 | 0.72 | 0%–13% | 0/150 | 2.03 |
| `deepeval.faithfulness` | 0.50 | 0.69 | 0.65 | 1%–19% | 13/554 | 14.28 |
| `embedding_relevance` | 0.65 | 0.99 | 0.94 | 2%–21% | 0/594 | 0.02 |
| `embedding_similarity` | 0.87 | 0.82 | 0.82 | 6%–30% | 0/580 | 0.01 |
| `exact_facts` | 0.50 | 0.76 | 0.77 | 3%–25% | 0/580 | 0.00 |
| `faithfulness_llm` | 0.75 | 1.00 | 1.00 | 0%–11% | 0/554 | 1.83 |
| `key_point_mean` | 0.07 | 0.99 | 0.98 | 0%–12% | 0/392 | 0.03 |
| `key_point_nli` | 0.00 | 0.97 | 0.89 | 0%–11% | 0/392 | 0.03 |
| `lettucedetect` | 0.63 | 0.63 | 0.60 | 1%–17% | 0/554 | 0.58 |
| `nli_correctness` | 0.00 | 0.95 | 0.93 | 2%–22% | 0/580 | 0.04 |
| `number_grounding` | 0.50 | 0.64 | 0.65 | 0%–12% | 0/554 | 0.00 |
| `ragas.answer_correctness` | 0.79 | 0.98 | 0.98 | 4%–27% | 0/580 | 6.23 |
| `ragas.answer_relevancy` | 0.64 | 0.98 | 0.93 | 1%–17% | 0/594 | 4.75 |
| `ragas.context_recall` | 1.00 | 0.81 | 0.76 | 0%–11% | 0/150 | 2.00 |
| `ragas.faithfulness` | 0.00 | 0.89 | 0.80 | 0%–11% | 0/554 | 4.51 |
| `relevance_llm` | 1.00 | 0.98 | 0.97 | 0%–11% | 0/594 | 1.50 |
| `rouge_l` | 0.42 | 0.69 | 0.72 | 7%–34% | 0/580 | 0.00 |
| `sentence_nli` | 0.06 | 0.81 | 0.78 | 0%–14% | 0/554 | 0.45 |
| `signal_ratio` | 0.20 | 0.45 | 0.40 | 1%–17% | 0/150 |  |
| `token_f1` | 0.53 | 0.74 | 0.76 | 4%–27% | 0/580 | 0.00 |
| `token_support` | 0.60 | 0.72 | 0.72 | 0%–13% | 0/554 | 0.00 |

## Ragas and DeepEval at a 0.5 threshold

These runs use a threshold of 0.5 rather than the dev-calibrated one. 0.5 is DeepEval's default. Ragas ships no threshold, so 0.5 is our choice.

| Metric | False alarms | Failure recall, mean across categories |
|---|---:|---:|
| `deepeval.answer_relevancy` | 0% | 100% |
| `deepeval.contextual_recall` | 1% | 61% |
| `deepeval.faithfulness` | 5% | 37% |
| `ragas.answer_correctness` | 0% | 76% |
| `ragas.answer_relevancy` | 0% | 20% |
| `ragas.context_recall` | 0% | 59% |
| `ragas.faithfulness` | 13% | 67% |

## Retrieval modes

These describe the sample pipeline's modes and don't test an evaluator, since gold labels define these metrics. All evidence means every gold quote appears in the top 5.

| Split | Mode | Recall@5 | MRR | nDCG@5 | All evidence |
|---|---|---:|---:|---:|---:|
| dev | dense | 0.62 | 0.52 | 0.50 | 53% |
| dev | bm25 | 0.67 | 0.64 | 0.58 | 57% |
| dev | hybrid | 0.64 | 0.54 | 0.52 | 58% |
| test | dense | 0.67 | 0.54 | 0.57 | 67% |
| test | bm25 | 0.67 | 0.61 | 0.62 | 70% |
| test | hybrid | 0.73 | 0.58 | 0.62 | 80% |

## Not run in version 1

Real generated answers as clean controls or failures, document-shift set, GLM judge comparison, `claim_nli`, `question_regeneration`, real generated-answer failures, memory control and synthetic corpus, chunks vs. full-document comparison, repeat-run reliability, external datasets, and the Ragas and DeepEval metrics outside `ragas.faithfulness`, `ragas.answer_relevancy`, `ragas.answer_correctness`, `ragas.context_recall`, `deepeval.faithfulness`, `deepeval.answer_relevancy` and `deepeval.contextual_recall`. No pairwise significance tests or cluster-bootstrap reporting were included, intervals shown are Wilson intervals at question level, and dollar cost per evaluator wasn't measured. Close differences aren't findings.
