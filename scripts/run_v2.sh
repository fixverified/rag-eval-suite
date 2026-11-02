#!/bin/zsh
set -a; source .env; set +a
export PYTHONPATH=src:scripts:. OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
J=gpt-6-luna
nice -n 10 .venv/bin/python scripts/run_v2.py 2>>data/v2/errors.log | tail -1
(cd scripts && PYTHONPATH=. nice -n 10 ../.venv-deepeval/bin/python lib_deepeval.py ../data/v2/tasks.jsonl ../data/v2/deepeval__$J.jsonl --judge $J --metrics deepeval.faithfulness deepeval.answer_relevancy 2>>../data/v2/errors.log)
(cd scripts && PYTHONPATH=. nice -n 10 ../.venv-ragas/bin/python lib_ragas.py ../data/v2/tasks.jsonl ../data/v2/ragas__$J.jsonl --judge $J --metrics ragas.faithfulness ragas.answer_relevancy ragas.answer_correctness 2>>../data/v2/errors.log)
echo finished
