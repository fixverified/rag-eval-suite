"""Run Ragas metrics at their shipped prompts on exported tasks. Requires the .venv-ragas environment."""

import argparse
import asyncio
import json
import os
import warnings
from pathlib import Path

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
warnings.filterwarnings("ignore")

from lib_common import run_all
from openai import AsyncOpenAI
from ragas.embeddings import HuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerAccuracy,
    AnswerCorrectness,
    AnswerRelevancy,
    ContextEntityRecall,
    ContextPrecision,
    ContextPrecisionWithoutReference,
    ContextRecall,
    ContextRelevance,
    FactualCorrectness,
    Faithfulness,
    ResponseGroundedness,
    SemanticSimilarity,
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tasks")
parser.add_argument("out")
parser.add_argument("--judge", required=True)
parser.add_argument("--metrics", nargs="*")
args = parser.parse_args()

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=4)
# gpt-6-luna only accepts its default temperature, and Ragas otherwise sets its own low default and a top_p.
llm = llm_factory(args.judge, client=client, temperature=1.0 if args.judge == "gpt-6-luna" else 0.0, top_p=1.0, seed=20261101, max_tokens=4000)
embeddings = HuggingFaceEmbeddings(model="BAAI/bge-small-en-v1.5")


def question_answer(t):
    return dict(user_input=t["question"], response=t["answer"])


def reference(t):
    return dict(user_input=t["question"], response=t["answer"], reference=t["gold"])


def has_gold(*stages):
    return lambda task: task["stage"] in stages and task["gold"] is not None


METRICS = {
    "ragas.faithfulness": dict(metric=Faithfulness(llm=llm), inputs=lambda t: dict(user_input=t["question"], response=t["answer"], retrieved_contexts=t["contexts"]), applies=lambda t: t["stage"] == "answer" and "faithful" in t["labels"]),
    "ragas.response_groundedness": dict(metric=ResponseGroundedness(llm=llm), inputs=lambda t: dict(response=t["answer"], retrieved_contexts=t["contexts"]), applies=lambda t: t["stage"] == "answer" and "faithful" in t["labels"]),
    "ragas.answer_relevancy": dict(metric=AnswerRelevancy(llm=llm, embeddings=embeddings), inputs=question_answer, applies=lambda t: t["stage"] == "answer" and "relevant" in t["labels"]),
    "ragas.answer_correctness": dict(metric=AnswerCorrectness(llm=llm, embeddings=embeddings), inputs=reference, applies=lambda t: t["stage"] == "answer" and "correct" in t["labels"] and t["gold"] is not None),
    "ragas.answer_accuracy": dict(metric=AnswerAccuracy(llm=llm), inputs=reference, applies=lambda t: t["stage"] == "answer" and "correct" in t["labels"] and t["gold"] is not None),
    "ragas.factual_correctness": dict(metric=FactualCorrectness(llm=llm), inputs=lambda t: dict(response=t["answer"], reference=t["gold"]), applies=lambda t: t["stage"] == "answer" and "correct" in t["labels"] and t["gold"] is not None),
    "ragas.semantic_similarity": dict(metric=SemanticSimilarity(embeddings=embeddings), inputs=lambda t: dict(response=t["answer"], reference=t["gold"]), applies=lambda t: t["stage"] == "answer" and "correct" in t["labels"] and t["gold"] is not None),
    "ragas.context_precision": dict(metric=ContextPrecision(llm=llm), inputs=lambda t: dict(user_input=t["question"], reference=t["gold"], retrieved_contexts=t["contexts"]), applies=has_gold("context")),
    "ragas.context_precision_no_reference": dict(metric=ContextPrecisionWithoutReference(llm=llm), inputs=lambda t: dict(user_input=t["question"], response=t["answer"], retrieved_contexts=t["contexts"]), applies=has_gold("context")),
    "ragas.context_recall": dict(metric=ContextRecall(llm=llm), inputs=lambda t: dict(user_input=t["question"], retrieved_contexts=t["contexts"], reference=t["gold"]), applies=has_gold("context")),
    "ragas.context_entity_recall": dict(metric=ContextEntityRecall(llm=llm), inputs=lambda t: dict(reference=t["gold"], retrieved_contexts=t["contexts"]), applies=has_gold("context")),
    "ragas.context_relevance": dict(metric=ContextRelevance(llm=llm), inputs=lambda t: dict(user_input=t["question"], retrieved_contexts=t["contexts"]), applies=lambda t: t["stage"] == "context"),
}
if args.metrics:
    METRICS = {name: value for name, value in METRICS.items() if name in args.metrics}


async def score_one(name, task):
    entry = METRICS[name]
    return (await entry["metric"].ascore(**entry["inputs"](task))).value


tasks = [json.loads(line) for line in open(args.tasks)]
asyncio.run(run_all(tasks, METRICS, Path(args.out), score_one))
