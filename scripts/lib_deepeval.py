"""Run DeepEval metrics at their shipped prompts on exported tasks. Requires the .venv-deepeval environment."""

import argparse
import asyncio
import json
import os
from pathlib import Path

os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"
os.environ.pop("DEEPEVAL_EVAL_MODE", None)

from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
)
from deepeval.models import GPTModel
from deepeval.test_case import LLMTestCase
from lib_common import run_all

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tasks")
parser.add_argument("out")
parser.add_argument("--judge", required=True)
parser.add_argument("--metrics", nargs="*")
args = parser.parse_args()

model = GPTModel(model=args.judge, api_key=os.environ["OPENAI_API_KEY"], temperature=1.0 if args.judge == "gpt-6-luna" else 0.0, generation_kwargs={"seed": 20261101, "max_completion_tokens": 4000})


def answer_case(t):
    return dict(input=t["question"], actual_output=t["answer"], retrieval_context=t["contexts"])


def context_case(t):
    return dict(input=t["question"], actual_output=t["answer"] or "", retrieval_context=t["contexts"], expected_output=t["gold"])


METRICS = {
    "deepeval.faithfulness": dict(cls=FaithfulnessMetric, case=answer_case, applies=lambda t: t["stage"] == "answer" and "faithful" in t["labels"]),
    # DeepEval 4.3.2 scores the share of contexts that agree, so higher is better. Its documentation confirms this direction.
    "deepeval.hallucination": dict(cls=HallucinationMetric, case=lambda t: dict(input=t["question"], actual_output=t["answer"], context=t["contexts"]), applies=lambda t: t["stage"] == "answer" and "faithful" in t["labels"]),
    "deepeval.answer_relevancy": dict(cls=AnswerRelevancyMetric, case=lambda t: dict(input=t["question"], actual_output=t["answer"]), applies=lambda t: t["stage"] == "answer" and "relevant" in t["labels"]),
    "deepeval.contextual_precision": dict(cls=ContextualPrecisionMetric, case=context_case, applies=lambda t: t["stage"] == "context" and t["gold"] is not None),
    "deepeval.contextual_recall": dict(cls=ContextualRecallMetric, case=context_case, applies=lambda t: t["stage"] == "context" and t["gold"] is not None),
    "deepeval.contextual_relevancy": dict(cls=ContextualRelevancyMetric, case=context_case, applies=lambda t: t["stage"] == "context"),
}
if args.metrics:
    METRICS = {name: value for name, value in METRICS.items() if name in args.metrics}


async def score_one(name, task):
    entry = METRICS[name]
    metric = entry["cls"](model=model, async_mode=False, include_reason=False)
    case = LLMTestCase(**entry["case"](task))
    # DeepEval's sync path makes blocking calls, so it runs in a worker thread.
    await asyncio.to_thread(metric.measure, case, _show_indicator=False)
    return metric.score


tasks = [json.loads(line) for line in open(args.tasks)]
asyncio.run(run_all(tasks, METRICS, Path(args.out), score_one))
