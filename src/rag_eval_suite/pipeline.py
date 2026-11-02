"""The sample RAG pipeline. It's here to produce realistic inputs, and the evaluators don't depend on it."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from functools import lru_cache
from pathlib import Path

import numpy as np

from .corpus import CORPUS_DIR, Chunk, build_chunks, document_text
from .models import ROOT, embed, rerank

MODES = ("dense", "bm25", "hybrid")
TOP_K = 5
CANDIDATES = 30
RRF_K = 60
PROMPT = """Answer the question using only the passages below. If the passages don't contain the answer, say that the passages do not contain it. Keep the answer to 1-3 sentences.

Question: {question}

Passages:
{passages}"""


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Retriever:
    """Indexes every chunk in a corpus directory. Embeddings are cached on disk."""

    def __init__(self, corpus_dir: Path = CORPUS_DIR) -> None:
        from rank_bm25 import BM25Okapi

        self.chunks: list[Chunk] = build_chunks(corpus_dir=corpus_dir)
        self.by_id = {c.id: c for c in self.chunks}
        self.bm25 = BM25Okapi([_tokens(c.text) for c in self.chunks])
        cache = ROOT / ".cache" / f"embeddings-{corpus_dir.name}-{len(self.chunks)}.npy"
        cache.parent.mkdir(exist_ok=True)
        if cache.exists():
            self.vectors = np.load(cache)
        else:
            self.vectors = np.array(embed([c.text for c in self.chunks]))
            np.save(cache, self.vectors)

    def _dense(self, query: str, count: int) -> list[str]:
        # bge-small's model card recommends this prefix for queries.
        vector = np.array(embed([f"Represent this sentence for searching relevant passages: {query}"])[0])
        return [self.chunks[i].id for i in np.argsort(-(self.vectors @ vector))[:count]]

    def _bm25(self, query: str, count: int) -> list[str]:
        return [self.chunks[i].id for i in np.argsort(-self.bm25.get_scores(_tokens(query)))[:count]]

    def retrieve(self, query: str, mode: str = "hybrid", k: int = TOP_K) -> list[Chunk]:
        if mode == "dense":
            return [self.by_id[i] for i in self._dense(query, k)]
        if mode == "bm25":
            return [self.by_id[i] for i in self._bm25(query, k)]
        if mode != "hybrid":
            raise ValueError(f"unknown mode {mode}")
        fused: dict[str, float] = {}
        for ranking in (self._dense(query, CANDIDATES), self._bm25(query, CANDIDATES)):
            for rank, chunk_id in enumerate(ranking, 1):
                fused[chunk_id] = fused.get(chunk_id, 0.0) + 1 / (RRF_K + rank)
        candidates = sorted(fused, key=fused.get, reverse=True)[:CANDIDATES]
        scores = rerank(query, [self.by_id[i].text for i in candidates])
        order = np.argsort(-np.array(scores))[:k]
        return [self.by_id[candidates[i]] for i in order]


def format_passages(chunks: Sequence[Chunk]) -> str:
    return "\n\n".join(f"[{c.id}]\n{c.text}" for c in chunks)


def generate(question: str, contexts: Sequence[Chunk], llm: Callable[[str], str]) -> str:
    return llm(PROMPT.format(question=question, passages=format_passages(contexts)))


def generate_from_documents(question: str, publications: Sequence[str], llm: Callable[[str], str]) -> str:
    """The full-context mode: hand the generator whole publications instead of chunks."""
    passages = "\n\n".join(f"[{p}]\n{document_text(p)}" for p in publications)
    return llm(PROMPT.format(question=question, passages=passages))


def generate_closed_book(question: str, llm: Callable[[str], str]) -> str:
    """No retrieval, used to find questions a model can answer from memory."""
    return llm(f"Answer in 1-3 sentences. If you don't know, say so.\n\nQuestion: {question}")
