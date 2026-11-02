# Version 3 results

Added after version 2. Both analyses use real answers from chunks or evidence-removed context, with version 2's AI labels. No human has reviewed these labels.

## Do LLM verdicts change between runs?

Each answer was judged 5 times by `gpt-6-luna` at temperature 1, using different seeds. Verdicts use the version 1 thresholds.

| Evaluator | Answers | Verdict changed | Rating changed | Good answers flagged, mean | Bad answers flagged, mean | Errors |
|---|---:|---:|---:|---:|---:|---:|
| `correctness_llm` | 119 | 2 (2%) | 5 (4%) | 2% | 100% | 0 |
| `faithfulness_llm` | 159 | 15 (9%) | 25 (16%) | 2% | 63% | 0 |

## Do better thresholds fix the cheap metrics?

Each evaluator's threshold was set on real good answers in 4 folds to allow at most 5% false alarms, then scored on the fifth, by question. Sample sizes are small, and AUROC here compares wrong or partial non-refusals with good answers, without thresholds.

| Evaluator | Good answers flagged | Wrong or partial answers caught | Refusals caught | AUROC |
|---|---:|---:|---:|---:|
| `correctness_llm` | 3/67 | 12/19 | 32/33 | 0.98 |
| `ragas.answer_correctness` | 5/67 | 9/19 | 33/33 | 0.91 |
| `nli_correctness` | 3/67 | 5/19 | 11/33 | 0.67 |
| `exact_facts` | 3/67 | 2/19 | 24/33 | 0.66 |
| `rouge_l` | 3/67 | 1/19 | 20/33 | 0.65 |
| `bleu` | 3/67 | 1/19 | 13/33 | 0.63 |
| `token_f1` | 3/67 | 1/19 | 12/33 | 0.63 |
| `embedding_similarity` | 5/67 | 5/19 | 10/33 | 0.48 |
