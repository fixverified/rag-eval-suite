"""Shared task loop for the library runners. Runs under each library's own environment, so standard library only."""

import asyncio
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CONCURRENCY = 15
TIMEOUT_SECONDS = 180


TRANSIENT = ("RateLimit", "RetryError", "APIConnection", "APITimeout", "InternalServerError", "TimeoutError", "LengthFinishReason")


def load_done(out: Path) -> set[tuple[str, str]]:
    """Temporary API failures produced no answer, so a rerun tries them again."""
    if not out.exists():
        return set()
    rows = map(json.loads, out.read_text().splitlines())
    return {(r["task_id"], r["evaluator"]) for r in rows if not (r["error"] or "").startswith(TRANSIENT)}


async def run_all(tasks: list[dict], metrics: dict, out: Path, score_one) -> None:
    """score_one(metric_name, task) returns a float. Exceptions and NaN are recorded as errors, never as scores."""
    # DeepEval's blocking calls run in worker threads, so the pool has to match the concurrency.
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(CONCURRENCY))
    done = load_done(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    gate = asyncio.Semaphore(CONCURRENCY)
    lock = asyncio.Lock()

    async def work(name: str, task: dict, handle) -> None:
        async with gate:
            started = time.monotonic()
            row = {"task_id": task["task_id"], "evaluator": name, "score": None, "error": None}
            try:
                score = await asyncio.wait_for(score_one(name, task), TIMEOUT_SECONDS)
                if score is None or (isinstance(score, float) and math.isnan(score)):
                    row["error"] = "nan"
                else:
                    row["score"] = float(score)
            except Exception as error:  # noqa: BLE001 - library errors are counted separately
                row["error"] = f"{type(error).__name__}: {error}"[:300]
            row["seconds"] = time.monotonic() - started
            async with lock:
                handle.write(json.dumps(row) + "\n")
                handle.flush()

    with out.open("a") as handle:
        await asyncio.gather(*(work(name, task, handle) for task in tasks for name in metrics if metrics[name]["applies"](task) and (task["task_id"], name) not in done))
