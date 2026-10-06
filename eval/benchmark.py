"""Benchmark retrieval ordering over a labeled question set.

Two modes:

  Engine mode (default) — query Basic Memory, then rerank with decision models.

      uv run python eval/benchmark.py --provider both --delay 3.2

  Replay mode — rerank a recorded candidate file; no engine or index needed.

      uv run python eval/benchmark.py --replay eval/demo/candidates.json --provider mercury --delay 3.2

Record a candidate file from a live run with `--record PATH`; `--provider none`
does a fast native-only pass. Provider runs need an OpenRouter key
(OPENROUTER_API_KEY or the OpenCode auth store). Engine mode also needs the
Basic Memory HTTP MCP service running (see scripts/start-bm-http.sh).

Each question is a dict: {id, q, project, accept[]}, where `accept` holds title
or path fragments that mark the expected note. A recorded file contains the same
fields plus a `candidates` list per question.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from pathlib import Path

import httpx

from acheron.bm import BMClient
from acheron.config import PROVIDERS, Config
from acheron.decisions import score_candidates
from acheron.ranking import fuse

HERE = Path(__file__).parent

CANDIDATE_FIELDS = ("title", "entity", "path", "file_path", "project", "snippet", "native_score")


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def rank_of(accept: list[str], results: list[dict]) -> int | None:
    for position, item in enumerate(results, 1):
        hay = norm(f"{item.get('title','')} {item.get('entity','')} {item.get('path','')}")
        if any(norm(a) in hay for a in accept):
            return position
    return None


def model_order(candidates: list[dict], scores: list[float | None]) -> list[dict]:
    order = sorted(
        range(len(candidates)),
        key=lambda i: (scores[i] is None, -(scores[i] or 0.0), i),
    )
    return [candidates[i] for i in order]


def trim(candidates: list[dict]) -> list[dict]:
    return [{key: item.get(key) for key in CANDIDATE_FIELDS} for item in candidates]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["mercury", "jev", "both", "none"],
        default="mercury",
        help="decision model(s) to run; 'none' is a native-only pass (useful with --record)",
    )
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help="search across all projects instead of each question's project",
    )
    parser.add_argument("--questions", default=str(HERE / "questions.json"))
    parser.add_argument("--out", default=None, help="save a results JSON file")
    parser.add_argument("--record", default=None, help="save native candidates for offline replay")
    parser.add_argument("--replay", default=None, help="replay a recorded candidate file")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="seconds between questions; Mercury's free tier allows 20 requests/minute",
    )
    args = parser.parse_args()

    if args.replay:
        questions = json.loads(Path(args.replay).read_text())["questions"]
    else:
        questions = json.loads(Path(args.questions).read_text())

    cfg = Config.from_env()
    providers = {
        "mercury": ["mercury"],
        "jev": ["jev"],
        "both": ["mercury", "jev"],
        "none": [],
    }[args.provider]
    if providers and not cfg.openrouter_key:
        raise SystemExit("No OpenRouter key in env or OpenCode auth store")

    bm = None if args.replay else BMClient(cfg.bm_url)
    http = httpx.AsyncClient() if providers else None
    methods = ["native"] + providers + [f"fuse_{p}" for p in providers]
    summary = {m: {"top1": 0, "top3": 0} for m in methods}
    latency: dict[str, list[float]] = {m: [] for m in methods}
    rows = []
    recorded = []

    for item in questions:
        if args.replay:
            candidates = trim(item["candidates"])
            native_rank = rank_of(item["accept"], candidates)
            latency["native"].append(0.0)
        else:
            project = None if args.all_projects else item["project"]
            started = time.time()
            candidates = await bm.search(
                item["q"], project=project, all_projects=True, page_size=10
            )
            latency["native"].append(time.time() - started)
            native_rank = rank_of(item["accept"], candidates)
            if args.record:
                recorded.append(
                    {
                        "id": item["id"],
                        "q": item["q"],
                        "accept": item["accept"],
                        "candidates": trim(candidates),
                    }
                )

        row = {
            "id": item["id"],
            "q": item["q"],
            "accept": item["accept"],
            "native_rank": native_rank,
        }
        for provider in providers:
            try:
                started = time.time()
                scores = await score_candidates(
                    http,
                    model=PROVIDERS[provider],
                    key=cfg.openrouter_key,
                    query=item["q"],
                    candidates=candidates,
                )
                latency[provider].append(time.time() - started)
                row[f"{provider}_rank"] = rank_of(item["accept"], model_order(candidates, scores))
                fused = fuse(candidates, scores)
                row[f"fuse_{provider}_rank"] = rank_of(item["accept"], fused)
            except Exception as exc:  # keep the benchmark running
                row[f"{provider}_error"] = str(exc)[:150]

        for method in methods:
            rank = row.get(f"{method}_rank")
            if isinstance(rank, int):
                if rank == 1:
                    summary[method]["top1"] += 1
                if rank <= 3:
                    summary[method]["top3"] += 1
        rows.append(row)
        print(
            f'{item["id"]:>2} ' + " ".join(f"{m}={row.get(f'{m}_rank')}" for m in methods)
            + f' | {item["q"][:52]}'
        )
        if args.delay:
            await asyncio.sleep(args.delay)

    print(f"\n=== SUMMARY (out of {len(questions)}) ===")
    for method in methods:
        print(f'{method:>12}: top1={summary[method]["top1"]:>2}  top3={summary[method]["top3"]:>2}')
    print(
        "mean latency s:",
        {m: round(sum(v) / len(v), 2) for m, v in latency.items() if v},
    )

    if args.record and recorded:
        Path(args.record).write_text(json.dumps({"questions": recorded}, indent=1) + "\n")
        print("recorded candidates:", args.record)
    if args.out:
        Path(args.out).write_text(
            json.dumps(
                {
                    "summary": summary,
                    "mean_latency_s": {m: sum(v) / len(v) for m, v in latency.items() if v},
                    "all_projects": args.all_projects,
                    "questions": len(questions),
                    "rows": rows,
                },
                indent=1,
            )
        )
        print("saved:", args.out)

    if bm is not None:
        await bm.close()
    if http is not None:
        await http.aclose()


if __name__ == "__main__":
    asyncio.run(main())
