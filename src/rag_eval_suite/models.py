"""Local models and a cached chat client, in the plain function shapes the evaluators expect."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache" / "llm.sqlite"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
NLI_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Model names with a slash use OpenRouter, which reports each call's cost. Others use the OpenAI API directly.
# OpenAI doesn't return a cost, so its spending is estimated from these dollars per million tokens.
OPENAI_PRICES = {
    "gpt-4.1-nano-2025-04-14": (0.10, 0.40),
    "gpt-4o-mini-2024-07-18": (0.15, 0.60),
    "gpt-4.1-mini-2025-04-14": (0.40, 1.60),
    "gpt-6-luna": (0.10, 0.50),
}
FIXED_TEMPERATURE = {"gpt-6-luna"}
TEMPERATURE = 0.0
MAX_TOKENS = 2000
SEED = 20261101
_lock = threading.Lock()


def _device() -> str:
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL, device=_device())


def embed(texts: Sequence[str]) -> list[list[float]]:
    return _embedder().encode(list(texts), normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()


@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANK_MODEL, device=_device())


def rerank(query: str, passages: Sequence[str]) -> list[float]:
    """Cross-encoder scores squashed to 0-1. This model outputs raw logits."""
    import math

    if not passages:
        return []
    logits = _reranker().predict([(query, p) for p in passages], batch_size=32, activation_fn=None, show_progress_bar=False)
    return [1 / (1 + math.exp(-float(x))) for x in logits]


@lru_cache(maxsize=4)
def _nli(model_name: str):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name).to(_device()).eval()
    labels = {name.lower(): index for index, name in model.config.id2label.items()}
    return tokenizer, model, labels["entailment"]


def nli(premise: str, hypothesis: str, model_name: str = NLI_MODEL) -> float:
    """Probability that the premise entails the hypothesis. Label order comes from the model's config."""
    import torch

    tokenizer, model, entailment = _nli(model_name)
    # Long premises get cut, never the claim being tested.
    inputs = tokenizer(premise, hypothesis, truncation="only_first", max_length=512, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        return torch.softmax(model(**inputs).logits[0], dim=-1)[entailment].item()


def lettuce_spans(contexts: Sequence[str], question: str, answer: str) -> list[dict]:
    return _lettuce().predict(context=list(contexts), question=question, answer=answer, output_format="spans")


@lru_cache(maxsize=1)
def _lettuce():
    from lettucedetect.models.inference import HallucinationDetector

    return HallucinationDetector(method="transformer", model_path="KRLabsOrg/lettucedect-base-modernbert-en-v1")


class LLM:
    """A chat model that caches replies on disk, so reruns are free and repeatable, and tracks spending."""

    def __init__(self, model: str, seed: int = SEED, temperature: float = TEMPERATURE) -> None:
        from openai import OpenAI

        self.model, self.seed, self.temperature = model, seed, temperature
        self.direct = "/" not in model
        if self.direct:
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], max_retries=6, timeout=180)
        else:
            self.client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=os.environ["OPENROUTER_API_KEY"], max_retries=6, timeout=180)
        CACHE.parent.mkdir(exist_ok=True)
        self.db = sqlite3.connect(CACHE, check_same_thread=False)
        self.db.execute("create table if not exists replies(key text primary key, model text, reply text, cost real, prompt_tokens int, completion_tokens int, seconds real, returned_model text, provider text)")
        self.calls = self.cached = 0
        self.cost = 0.0

    def __call__(self, prompt: str) -> str:
        key = hashlib.sha256(json.dumps([self.model, self.seed, self.temperature, prompt]).encode()).hexdigest()
        with _lock:
            row = self.db.execute("select reply from replies where key = ?", (key,)).fetchone()
        if row:
            self.cached += 1
            return row[0]
        started = time.monotonic()
        options: dict = {"seed": self.seed}
        if self.direct:
            options["max_completion_tokens"] = MAX_TOKENS
        else:
            options["max_tokens"] = MAX_TOKENS
            options["extra_body"] = {"usage": {"include": True}}
        if self.model not in FIXED_TEMPERATURE:
            options["temperature"] = self.temperature
        response = self.client.chat.completions.create(model=self.model, messages=[{"role": "user", "content": prompt}], **options)
        if not response.choices or response.choices[0].message.content is None:
            raise RuntimeError(f"no content from {self.model}: {getattr(response, 'error', None)}")
        reply = response.choices[0].message.content
        usage = response.usage.model_dump() if response.usage else {}
        if self.direct:
            input_price, output_price = OPENAI_PRICES[self.model]
            cost = (usage.get("prompt_tokens", 0) * input_price + usage.get("completion_tokens", 0) * output_price) / 1e6
        else:
            cost = float(usage.get("cost") or 0.0)
        with _lock:
            self.db.execute(
                "insert or replace into replies values (?,?,?,?,?,?,?,?,?)",
                (key, self.model, reply, cost, usage.get("prompt_tokens"), usage.get("completion_tokens"), time.monotonic() - started, response.model, getattr(response, "provider", None)),
            )
            self.db.commit()
            self.calls += 1
            self.cost += cost
        return reply


def total_cost() -> float:
    if not CACHE.exists():
        return 0.0
    db = sqlite3.connect(CACHE)
    try:
        return float(db.execute("select coalesce(sum(cost), 0) from replies").fetchone()[0])
    finally:
        db.close()
