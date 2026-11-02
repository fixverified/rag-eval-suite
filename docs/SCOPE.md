# Evaluator scope

Fixed before dev results exist. Each evaluator is scored only on its dimension. Others count as out of scope, and a question where a dimension is undefined counts as N/A rather than a pass or a miss. Ragas and DeepEval dimensions follow each library's documented purpose for the metric.

Version 1 ran only `ragas.faithfulness`, `ragas.answer_relevancy`, `ragas.answer_correctness`, `ragas.context_recall`, `deepeval.faithfulness`, `deepeval.answer_relevancy` and `deepeval.contextual_recall` from the libraries, and didn't run `claim_nli` or `question_regeneration`. The other metrics below are planned, with no results yet.

## Answer dimensions

| Dimension | Failures with a bad label | This repo | Ragas 0.4.3 | DeepEval 4.3.2 |
|---|---|---|---|---|
| **Faithful** | wrong number, negation, unsupported addition, wrong condition, unsupported but true, wrongful answer | `token_support`, `number_grounding`, `sentence_nli`, `claim_nli`, `lettucedetect`, `faithfulness_llm` | `Faithfulness`, `ResponseGroundedness` | `FaithfulnessMetric`, `HallucinationMetric` |
| **Relevant** | off-topic | `embedding_relevance`, `cross_encoder_relevance`, `question_regeneration`, `relevance_llm` | `AnswerRelevancy` | `AnswerRelevancyMetric` |
| **Correct** | wrong number, negation, wrong condition, off-topic, wrongful refusal | `exact_facts`, `token_f1`, `rouge_l`, `bleu`, `embedding_similarity`, `nli_correctness`, `correctness_llm` | `AnswerCorrectness`, `AnswerAccuracy`, `FactualCorrectness`, `SemanticSimilarity` | None |
| **Complete** | off-topic, incomplete, wrongful refusal | `key_point_nli`, `key_point_mean`, `completeness_llm` | None | None |
| **Abstention** | wrongful answer, wrongful refusal | `abstention_rule`, `abstention_reranker`, `abstention_llm` | None | None |
| **Citation** | bad citation | `citations_exist`, `citation_coverage`, `citation_support` | None | None |

Exploit families use the labels in `src/rag_eval_suite/schema.py`, and are reported separately from failures.

## Context dimension

The label is whether the gold evidence is in the context, which is checked against verified quotes on real retrieved contexts, plus contexts with gold evidence removed. This asks whether an evaluator notices missing evidence without being given the quote.

| This repo | Ragas 0.4.3 | DeepEval 4.3.2 |
|---|---|---|
| `context_sufficiency_llm`, `context_relevance_reranker`, `signal_ratio` | `ContextRecall`, `ContextPrecision`, `ContextPrecisionWithoutReference`, `ContextEntityRecall`, `ContextRelevance` | `ContextualRecallMetric`, `ContextualPrecisionMetric`, `ContextualRelevancyMetric` |

Some of these target other properties, such as ordering or noise, so they're still measured here but marked as indirect in results. `ContextRecall` and `ContextualRecallMetric` target missing evidence directly, and can use a reference answer.

## Descriptive only

Rank metrics (recall@k, precision@k, hit rate, MRR, MAP, nDCG) and `evidence_coverage` are defined by gold labels, so they describe retrieval modes rather than detect anything. Query term overlap, duplicate rate, source diversity, context utilization, and consistency metrics have no failure labels.

## Not run

| Metric | Why |
|---|---|
| Ragas `NoiseSensitivity` | Needs 2N+3 calls per sample and targets a different question, so it isn't comparable with these dimensions |
| DeepEval `ConversationCompletenessMetric` | Applies only to conversations |
