import json

import pytest
from mcp.server.fastmcp.tools.base import Tool as FastMCPTool
from mcp.types import CallToolResult, TextContent, Tool

from acheron import server
from acheron.bm import BMError
from acheron.config import CANDIDATES_MAX, LIMIT_MAX, Config

NOTE_SCHEMA = {
    "properties": {
        "identifier": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "description": "Note identifier.",
        },
        "depth": {"default": 1, "type": "integer", "description": "Recursion depth."},
    },
    "required": ["identifier"],
    "type": "object",
    "additionalProperties": False,
}


def engine_tool(name, schema=None):
    return Tool(name=name, description=f"{name} description", inputSchema=schema or {})


def test_policy_hides_the_folded_search_and_connector_adapters():
    tools = [
        engine_tool("search_notes"),
        engine_tool("search"),
        engine_tool("fetch"),
        engine_tool("read_note", NOTE_SCHEMA),
        engine_tool("write_note", NOTE_SCHEMA),
    ]
    assert [tool.name for tool in server.visible_tools(tools)] == ["read_note", "write_note"]


def test_proxy_schema_mirrors_engine_parameters():
    fn = server.proxy_fn("read_note", NOTE_SCHEMA, forward=None)
    tool = FastMCPTool.from_function(fn, name="read_note", description="read")
    params = tool.parameters
    assert set(params["properties"]) == {"identifier", "depth"}
    assert params["properties"]["depth"]["description"] == "Recursion depth."
    assert (
        params["properties"]["identifier"]["anyOf"]
        == NOTE_SCHEMA["properties"]["identifier"]["anyOf"]
    )
    assert params["required"] == ["identifier"]


async def test_proxy_forwards_engine_name_and_arguments():
    seen = {}

    async def fake_forward(name, args):
        seen["name"] = name
        seen["args"] = args
        return CallToolResult(content=[TextContent(type="text", text="ok")])

    fn = server.proxy_fn("read_note", NOTE_SCHEMA, forward=fake_forward)
    tool = FastMCPTool.from_function(fn, name="read_note", description="read")
    result = await tool.run({"identifier": "demo/notes/a", "depth": 2})
    assert seen == {
        "name": "read_note",
        "args": {"identifier": "demo/notes/a", "depth": 2},
    }
    assert result.content[0].text == "ok"


async def test_proxy_defaults_come_from_the_engine_schema():
    seen = {}

    async def fake_forward(name, args):
        seen["args"] = args
        return "ok"

    fn = server.proxy_fn("read_note", NOTE_SCHEMA, forward=fake_forward)
    tool = FastMCPTool.from_function(fn, name="read_note", description="read")
    await tool.run({"identifier": "x"})
    assert seen["args"] == {"identifier": "x", "depth": 1}


class FakeEngine:
    def __init__(self, payload=None, error=None, tools=None):
        self.payload = payload or {}
        self.error = error
        self.tools = tools or []
        self.calls = []

    async def list_tools(self):
        return self.tools

    async def search_payload(self, query, **kwargs):
        self.calls.append(("search_payload", query, kwargs))
        if self.error:
            raise self.error
        return self.payload

    async def search(self, query, **kwargs):
        self.calls.append(("search", query, kwargs))
        if self.error:
            raise self.error
        return [
            {
                "title": "Memory",
                "entity": "e",
                "path": "p",
                "file_path": "f",
                "project": "demo",
                "snippet": "s",
                "native_score": 0.9,
            }
        ]


def use_engine(monkeypatch, engine):
    async def fake_get_bm(url):
        return engine

    monkeypatch.setattr(server, "_get_bm", fake_get_bm)
    monkeypatch.setattr(server.Config, "from_env", classmethod(lambda cls: Config()))


async def test_filter_only_search_passes_through_natively(monkeypatch):
    engine = FakeEngine(payload={"results": [{"title": "A"}], "count": 1})
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(tags=["ai"]))
    assert out["ranking"] == "native"
    assert out["mode"] == "filter"
    assert out["results"] == [{"title": "A"}]
    kind, query, kwargs = engine.calls[0]
    assert kind == "search_payload"
    assert query is None
    assert kwargs["filters"] == {"tags": ["ai"]}
    assert kwargs["page_size"] == 5


async def test_query_search_still_reranks_with_fallback(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(query="memory palace"))
    assert out["fallback"] is True
    assert out["ranking"] == "native"
    assert out["count"] == 1
    kind, query, kwargs = engine.calls[0]
    assert kind == "search"
    assert query == "memory palace"
    assert kwargs["filters"] == {}


async def test_filters_ride_along_with_a_query(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    await server.context_search(query="x", tags=["a"], status="active")
    assert engine.calls[0][2]["filters"] == {"tags": ["a"], "status": "active"}


async def test_no_query_and_no_filters_asks_for_one(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search())
    assert "query" in out["error"].lower()
    assert engine.calls == []


async def test_oversized_requests_clamp_to_the_hard_ceiling(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    await server.context_search(query="x", limit=10_000, candidates=10_000)
    assert engine.calls[0][2]["page_size"] == CANDIDATES_MAX


async def test_clamped_requests_disclose_the_clamp_in_the_payload(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(query="x", limit=10_000, candidates=10_000))
    assert out["clamped"] == {
        "limit": {"requested": 10_000, "effective": LIMIT_MAX},
        "candidates": {"requested": 10_000, "effective": CANDIDATES_MAX},
    }


async def test_unclamped_requests_carry_no_disclosure(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(query="x"))
    assert "clamped" not in out


async def test_filter_only_clamped_requests_disclose_the_clamp(monkeypatch):
    engine = FakeEngine(payload={"results": [], "count": 0})
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(tags=["ai"], limit=10_000))
    assert out["clamped"]["limit"] == {"requested": 10_000, "effective": LIMIT_MAX}


async def test_zero_and_negative_requests_clamp_to_one(monkeypatch):
    engine = FakeEngine()
    use_engine(monkeypatch, engine)
    await server.context_search(query="x", limit=-5, candidates=0)
    assert engine.calls[0][2]["page_size"] == 1


async def test_filter_only_page_size_is_clamped(monkeypatch):
    engine = FakeEngine(payload={"results": [], "count": 0})
    use_engine(monkeypatch, engine)
    await server.context_search(tags=["ai"], limit=10_000)
    assert engine.calls[0][2]["page_size"] == LIMIT_MAX


async def test_engine_down_returns_a_clean_product_error(monkeypatch):
    engine = FakeEngine(error=BMError("connection refused"))
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(query="x"))
    assert out["error"] == server.ENGINE_DOWN


async def test_engine_rejection_surfaces_its_own_message(monkeypatch):
    engine = FakeEngine(error=BMError("bad filter", kind="engine"))
    use_engine(monkeypatch, engine)
    out = json.loads(await server.context_search(query="x"))
    assert out["error"] == "bad filter"


class Recorder:
    def __init__(self):
        self.names = []

    def add_tool(self, fn, **kwargs):
        self.names.append(kwargs["name"])


async def test_register_proxies_applies_the_policy():
    engine = FakeEngine(tools=[engine_tool("search_notes"), engine_tool("read_note", NOTE_SCHEMA)])
    rec = Recorder()
    assert await server.register_proxies(server=rec, client=engine) == 1
    assert rec.names == ["read_note"]


class TwoNoteEngine(FakeEngine):
    """Two candidates, so model order and fused order are distinguishable."""

    async def search(self, query, **kwargs):
        self.calls.append(("search", query, kwargs))
        return [
            {
                "title": title,
                "entity": "e",
                "path": title.lower(),
                "file_path": "f",
                "project": "demo",
                "snippet": "s",
                "native_score": native,
            }
            for title, native in (("First", 0.9), ("Second", 0.8))
        ]


def use_scorer(monkeypatch, cfg, scores=None, error=None):
    """Wire a two-note engine and a recording scorer under the given config."""
    seen = []

    async def fake_get_bm(url):
        return TwoNoteEngine()

    async def fake_score(client, **kwargs):
        seen.append(kwargs)
        if error:
            raise error
        return scores if scores is not None else [1.0, 3.0]

    monkeypatch.setattr(server, "_get_bm", fake_get_bm)
    monkeypatch.setattr(server.Config, "from_env", classmethod(lambda cls: cfg))
    monkeypatch.setattr(server, "score_candidates", fake_score)
    return seen


LOCAL_URL = "http://127.0.0.1:9931/v1/systemone"
VENDOR_URL = "https://api.example.test/v1/systemone"


@pytest.mark.parametrize(
    ("provider", "model"),
    [
        ("mercury", "inception/mercury-decide:free"),
        ("perplexity", "perplexity/pplx-decider-v1.1-27b"),
        ("jev", "typesafe/jev-1.13"),
    ],
)
async def test_auto_ranking_uses_model_order_for_every_preset(monkeypatch, provider, model):
    cfg = Config(provider=provider, model=model, openrouter_key="or-key")
    use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q"))
    assert out["ranking"] == "model"
    assert [item["title"] for item in out["results"]] == ["Second", "First"]


async def test_auto_ranking_uses_model_order_for_a_custom_endpoint(monkeypatch):
    cfg = Config(provider="custom", model="openjev", decisions_url=LOCAL_URL)
    use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q"))
    assert out["ranking"] == "model"
    assert [item["title"] for item in out["results"]] == ["Second", "First"]


async def test_explicit_fuse_ranking_is_still_honoured(monkeypatch):
    cfg = Config(
        provider="mercury",
        model="inception/mercury-decide:free",
        openrouter_key="or-key",
        ranking="fuse",
    )
    use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q"))
    assert out["ranking"] == "fuse"
    assert [item["title"] for item in out["results"]] == ["First", "Second"]


async def test_default_endpoint_gets_the_openrouter_url_and_key(monkeypatch):
    cfg = Config(openrouter_key="or-key")
    seen = use_scorer(monkeypatch, cfg)
    await server.context_search(query="q")
    assert seen[0]["url"] == "https://openrouter.ai/api/alpha/decisions"
    assert seen[0]["key"] == "or-key"
    assert seen[0]["model"] == "inception/mercury-decide:free"


async def test_local_endpoint_is_called_without_any_key(monkeypatch):
    cfg = Config(
        provider="custom", model="openjev", decisions_url=LOCAL_URL, openrouter_key="or-key"
    )
    seen = use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q"))
    assert out["fallback"] is False
    assert seen[0]["url"] == LOCAL_URL
    assert seen[0]["key"] is None
    assert seen[0]["model"] == "openjev"


async def test_vendor_endpoint_gets_the_dedicated_key_not_the_openrouter_key(monkeypatch):
    cfg = Config(
        provider="custom",
        model="jev-latest",
        decisions_url=VENDOR_URL,
        decisions_key="vendor-key",
        openrouter_key="or-key",
    )
    seen = use_scorer(monkeypatch, cfg)
    await server.context_search(query="q")
    assert seen[0]["url"] == VENDOR_URL
    assert seen[0]["key"] == "vendor-key"


async def test_remote_endpoint_without_a_key_falls_open_without_calling_it(monkeypatch):
    cfg = Config(
        provider="custom", model="jev-latest", decisions_url=VENDOR_URL, openrouter_key="or-key"
    )
    seen = use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q"))
    assert seen == []
    assert out["fallback"] is True
    assert out["ranking"] == "native"
    assert out["provider"] == "native (no key for the configured decision endpoint)"
    assert [item["title"] for item in out["results"]] == ["First", "Second"]


async def test_failing_custom_endpoint_falls_open_to_native_order(monkeypatch):
    cfg = Config(provider="custom", model="openjev", decisions_url=LOCAL_URL)
    use_scorer(monkeypatch, cfg, error=server.DecisionsError("decisions API 500: down"))
    out = json.loads(await server.context_search(query="q"))
    assert out["fallback"] is True
    assert out["ranking"] == "native"
    assert [item["title"] for item in out["results"]] == ["First", "Second"]


async def test_per_call_preset_override_uses_openrouter_not_the_custom_endpoint(monkeypatch):
    cfg = Config(
        provider="custom",
        model="openjev",
        decisions_url=LOCAL_URL,
        decisions_key="vendor-key",
        openrouter_key="or-key",
    )
    seen = use_scorer(monkeypatch, cfg)
    await server.context_search(query="q", provider="perplexity")
    assert seen[0]["url"] == "https://openrouter.ai/api/alpha/decisions"
    assert seen[0]["key"] == "or-key"
    assert seen[0]["model"] == "perplexity/pplx-decider-v1.1-27b"


@pytest.mark.parametrize(
    "attempt",
    [
        "https://evil.example.test/x",
        "http://127.0.0.1:9931/v1/systemone",
        "typesafe/jev-1.13",
        "openjev",
        "custom",
    ],
)
async def test_per_call_provider_cannot_name_an_endpoint_or_model(monkeypatch, attempt):
    cfg = Config(openrouter_key="or-key")
    seen = use_scorer(monkeypatch, cfg)
    out = json.loads(await server.context_search(query="q", provider=attempt))
    assert seen == []
    assert out["ranking"] == "native"


def test_search_description_does_not_name_a_default_model():
    tool = server.mcp._tool_manager.get_tool("context_search")
    assert "Mercury" not in tool.description
