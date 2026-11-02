"""Load the frozen page text, clean PDF artifacts, split it into chunks, and locate evidence quotes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus" / "text"
CHUNK_WORDS = 180
OVERLAP_WORDS = 40
# pypdf splits letters after kerned capitals, as in "T able" and "Y ou". These capitals are never one-letter words here.
KERNING = re.compile(r"\b([TYVWPF]) (?=[a-z])")
LINE_HYPHEN = re.compile(r"(?<=[a-z])-\n(?=[a-z])")
SENTENCE_END = re.compile(r"(?<=[.!?:])\s+")


def clean_page(text: str) -> str:
    text = KERNING.sub(r"\1", text)
    text = LINE_HYPHEN.sub("", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def normalize(text: str) -> str:
    """Normalize for comparing quotes with page text: case, whitespace, curly quotes and hyphens."""
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    text = re.sub(r"-\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class Chunk:
    id: str
    publication: str
    page: int
    text: str


def load_pages(publications: list[str] | None = None, corpus_dir: Path = CORPUS_DIR) -> list[dict]:
    pages = []
    for path in sorted(corpus_dir.glob("*.jsonl")):
        if publications is not None and path.stem not in publications:
            continue
        for line in path.read_text().splitlines():
            row = json.loads(line)
            pages.append({**row, "text": clean_page(row["text"])})
    return pages


def chunk_page(page: dict, chunk_words: int = CHUNK_WORDS, overlap_words: int = OVERLAP_WORDS) -> list[Chunk]:
    sentences = []
    for sentence in SENTENCE_END.split(page["text"]):
        words = sentence.split()
        # Tables have no sentence breaks, so long runs are split by word count to keep chunks a usable size.
        sentences += [" ".join(words[i : i + chunk_words]) for i in range(0, len(words), chunk_words)]
    chunks: list[list[str]] = []
    current: list[str] = []
    for sentence in sentences:
        current.append(sentence)
        if sum(len(s.split()) for s in current) >= chunk_words:
            chunks.append(current)
            overlap: list[str] = []
            for previous in reversed(current):
                if sum(len(s.split()) for s in overlap) >= overlap_words:
                    break
                overlap.insert(0, previous)
            current = overlap
    if current and (not chunks or current != chunks[-1][-len(current) :]):
        chunks.append(current)
    return [
        Chunk(f"{page['publication']}-p{page['page']}-c{index}", page["publication"], page["page"], " ".join(body))
        for index, body in enumerate(chunks)
    ]


def build_chunks(publications: list[str] | None = None, corpus_dir: Path = CORPUS_DIR) -> list[Chunk]:
    return [chunk for page in load_pages(publications, corpus_dir) for chunk in chunk_page(page)]


def document_text(publication: str, corpus_dir: Path = CORPUS_DIR) -> str:
    return "\n\n".join(page["text"] for page in load_pages([publication], corpus_dir))


def quote_on_page(quote: str, publication: str, page: int, corpus_dir: Path = CORPUS_DIR) -> bool:
    pages = [p for p in load_pages([publication], corpus_dir) if p["page"] == page]
    return bool(pages) and normalize(quote) in normalize(pages[0]["text"])
