#!/bin/zsh
# Version 1 run on one split. Local models use one process and two threads, so the machine stays usable.
D=$1; R=$2; mkdir -p "$R"
set -a; source .env; set +a
export PYTHONPATH=src:scripts:. OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
J=gpt-6-luna
(cd scripts && PYTHONPATH=. nice -n 10 ../.venv-deepeval/bin/python lib_deepeval.py "../$D/tasks.jsonl" "../$R/deepeval__$J.jsonl" --judge $J --metrics deepeval.faithfulness deepeval.answer_relevancy deepeval.contextual_recall 2>>"../$R/errors.log") &
nice -n 10 .venv/bin/python scripts/run_answer.py "$D" "$R/own_llm__$J.jsonl" --kinds llm --judge $J --only faithfulness_llm relevance_llm correctness_llm completeness_llm abstention_llm 2>>"$R/errors.log" | tail -1 &
wait
nice -n 10 .venv/bin/python scripts/run_answer.py "$D" "$R/own_local.jsonl" --kinds heuristic local 2>>"$R/errors.log" | tail -1
nice -n 10 .venv/bin/python scripts/run_context.py "$D/tasks.jsonl" "$R/own_context__$J.jsonl" --judge $J 2>>"$R/errors.log" | tail -1
(cd scripts && PYTHONPATH=. nice -n 10 ../.venv-ragas/bin/python lib_ragas.py "../$D/tasks.jsonl" "../$R/ragas__$J.jsonl" --judge $J --metrics ragas.faithfulness ragas.answer_relevancy ragas.answer_correctness ragas.context_recall 2>>"../$R/errors.log")
echo finished
