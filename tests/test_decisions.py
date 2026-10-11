import json

import httpx
import pytest

from acheron.decisions import (
    QUERY_CHARS,
    RUBRIC,
    TITLE_CHARS,
    UNTRUSTED_LINE,
    DecisionsError,
    build_payload,
    parse_scores,
    score_candidates,
)


def test_build_payload_shape_and_truncation():
    cands = [
        {"title": "One", "snippet": "x" * 900},
        {"title": "Two", "snippet": "short"},
    ]
    payload = build_payload("inception/mercury-decide:free", "find things", cands)
    assert payload["model"] == "inception/mercury-decide:free"
    assert "find things" in payload["state"]
    assert set(payload["questions"]) == {"c1", "c2"}
    q1 = payload["questions"]["c1"]
    assert q1["type"] == "score"
    assert q1["criteria"] == RUBRIC
    assert "One" in q1["instructions"]
    assert len(q1["instructions"].splitlines()[-1]) <= 500


def test_parse_scores_handles_missing_answers():
    data = {"answers": {"c1": {"score": 2.5}, "c3": {"score": 0.0}}}
    assert parse_scores(data, 3) == [2.5, None, 0.0]


def test_build_payload_caps_title_and_query_and_marks_content_untrusted():
    payload = build_payload("m", "q" * 900, [{"title": "T" * 900, "snippet": "s"}])
    q1 = payload["questions"]["c1"]
    assert "T" * TITLE_CHARS in q1["instructions"]
    assert "T" * (TITLE_CHARS + 1) not in q1["instructions"]
    assert "q" * QUERY_CHARS in q1["instructions"]
    assert "q" * (QUERY_CHARS + 1) not in q1["instructions"]
    assert UNTRUSTED_LINE in q1["instructions"]
    assert "q" * QUERY_CHARS in payload["state"]
    assert "q" * (QUERY_CHARS + 1) not in payload["state"]


async def test_score_candidates_posts_and_parses():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"answers": {"c1": {"score": 3.0}, "c2": {"score": 1.0}}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    cands = [{"title": "One", "snippet": "a"}, {"title": "Two", "snippet": "b"}]
    scores = await score_candidates(
        client,
        model="typesafe/jev-1.13",
        key="test-key",
        query="q",
        candidates=cands,
    )
    assert scores == [3.0, 1.0]
    assert captured["url"] == "https://openrouter.ai/api/alpha/decisions"
    assert captured["auth"] == "Bearer test-key"
    assert captured["body"]["model"] == "typesafe/jev-1.13"
    await client.aclose()


async def test_score_candidates_raises_on_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(DecisionsError):
        await score_candidates(
            client,
            model="m",
            key="k",
            query="q",
            candidates=[{"title": "One", "snippet": "a"}],
        )
    await client.aclose()


async def test_score_candidates_wraps_transport_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(DecisionsError):
        await score_candidates(
            client,
            model="m",
            key="k",
            query="q",
            candidates=[{"title": "One", "snippet": "a"}],
        )
    await client.aclose()


async def test_score_candidates_wraps_unparseable_success_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(DecisionsError):
        await score_candidates(
            client,
            model="m",
            key="k",
            query="q",
            candidates=[{"title": "One", "snippet": "a"}],
        )
    await client.aclose()


async def test_score_candidates_retries_rate_limit_once():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, text="rate limited")
        return httpx.Response(200, json={"answers": {"c1": {"score": 2.0}}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scores = await score_candidates(
        client,
        model="m",
        key="k",
        query="q",
        candidates=[{"title": "One", "snippet": "a"}],
        retry_delay=0.0,
    )
    assert scores == [2.0]
    assert calls["count"] == 2
    await client.aclose()
