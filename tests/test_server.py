import json

from mcp.server.fastmcp.tools.base import Tool as FastMCPTool
from mcp.types import CallToolResult, TextContent, Tool

from acheron import server
from acheron.bm import BMError
from acheron.config import Config

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
