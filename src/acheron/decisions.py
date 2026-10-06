from __future__ import annotations

import asyncio

import httpx

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"

RUBRIC = [
    "unrelated",
    "same topic without answering",
    "useful supporting evidence",
    "direct answer",
]

SNIPPET_CHARS = 500


class DecisionsError(RuntimeError):
    pass


def build_payload(model: str, query: str, candidates: list[dict]) -> dict:
    questions = {}
    for i, cand in enumerate(candidates, 1):
        snippet = (cand.get("snippet") or "")[:SNIPPET_CHARS]
        questions[f"c{i}"] = {
            "type": "score",
            "instructions": (
                f"Query: {query}\n"
                f"Candidate {i} - {cand.get('title', '')}\n"
                f"{snippet}"
            ),
            "criteria": RUBRIC,
        }
    return {
        "model": model,
        "state": f"Rank candidates for the query: {query}",
        "questions": questions,
    }


def parse_scores(data: dict, count: int) -> list[float | None]:
    answers = (data or {}).get("answers") or {}
    scores: list[float | None] = []
    for i in range(1, count + 1):
        answer = answers.get(f"c{i}") or {}
        score = answer.get("score")
        scores.append(float(score) if isinstance(score, (int, float)) else None)
    return scores


async def score_candidates(
    client: httpx.AsyncClient,
    *,
    model: str,
    key: str,
    query: str,
    candidates: list[dict],
    timeout: float = 60.0,
    retries: int = 1,
    retry_delay: float = 2.0,
) -> list[float | None]:
    payload = build_payload(model, query, candidates)
    for attempt in range(retries + 1):
        response = await client.post(
            DECISIONS_URL,
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout,
        )
        if response.status_code < 400:
            return parse_scores(response.json(), len(candidates))
        # Retry rate limits and server errors once; everything else raises now.
        if attempt < retries and (response.status_code == 429 or response.status_code >= 500):
            await asyncio.sleep(retry_delay)
            continue
        raise DecisionsError(f"decisions API {response.status_code}: {response.text[:200]}")
    raise DecisionsError("decisions API: retries exhausted")  # pragma: no cover
