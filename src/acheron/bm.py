from __future__ import annotations

import asyncio
import json
from typing import Any

try:  # SDK export name varies across versions
    from mcp.client.streamable_http import streamable_http_client as _streamable_client
except ImportError:  # pragma: no cover
    from mcp.client.streamable_http import streamablehttp_client as _streamable_client  # type: ignore

from mcp import ClientSession


class BMError(RuntimeError):
    """An engine failure: `transport` when the service is unreachable, `engine` when it rejected the call."""

    def __init__(self, message: str, *, kind: str = "transport") -> None:
        super().__init__(message)
        self.kind = kind


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def normalize_results(payload: dict) -> list[dict[str, Any]]:
    results = (payload or {}).get("results") or []
    normalized = []
    for item in results:
        normalized.append(
            {
                "title": item.get("title") or "",
                "entity": item.get("entity") or item.get("permalink") or "",
                "path": item.get("permalink") or item.get("entity") or "",
                "file_path": item.get("file_path") or "",
                "project": item.get("project") or "",
                "snippet": _clean(item.get("matched_chunk") or item.get("content") or ""),
                "native_score": item.get("score"),
            }
        )
    return normalized


def _text_of(result: Any) -> str:
    for content in getattr(result, "content", []) or []:
        text = getattr(content, "text", None)
        if text:
            return text
    return ""


def _is_error(result: Any) -> bool:
    if hasattr(result, "is_error"):
        return bool(result.is_error)
    return bool(getattr(result, "isError", False))


def _search_args(
    query: str | None,
    project: str | None,
    all_projects: bool,
    page_size: int,
    filters: dict[str, Any] | None,
) -> dict[str, Any]:
    args: dict[str, Any] = {"page_size": page_size, "output_format": "json"}
    if query:
        args["query"] = query
    for key, value in (filters or {}).items():
        if value is not None:
            args[key] = value
    if project:
        args["project"] = project
    else:
        args["search_all_projects"] = all_projects
    return args


class BMClient:
    """MCP client for a long-lived `bm mcp --transport streamable-http` service.

    Connects per call. The Basic Memory *service* holds the warm index and
    embedding model; the loopback handshake is cheap, and a per-call session
    avoids holding an async task group open across MCP tool-call tasks (which
    makes shutdown hang).
    """

    def __init__(self, url: str) -> None:
        self.url = url

    async def close(self) -> None:  # nothing persistent to release
        return None

    async def call_tool(self, name: str, args: dict[str, Any], *, retries: int = 1) -> Any:
        """Call any engine tool and return the raw result, so callers can forward it verbatim."""
        last_error: Exception | None = None
        for _ in range(retries + 1):
            try:
                async with _streamable_client(self.url) as streams:
                    read_stream, write_stream = streams[0], streams[1]
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        return await session.call_tool(name, args)
            except Exception as exc:
                last_error = exc
        raise BMError(str(last_error)) from last_error

    async def list_tools(self, attempts: int = 3) -> list[Any]:
        """Discover the engine's tools, retrying briefly while the service starts."""
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                async with _streamable_client(self.url) as streams:
                    read_stream, write_stream = streams[0], streams[1]
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        listed = await session.list_tools()
                        return list(listed.tools)
            except Exception as exc:
                last_error = exc
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise BMError(str(last_error)) from last_error

    async def search_payload(
        self,
        query: str | None,
        *,
        project: str | None = None,
        all_projects: bool = True,
        page_size: int = 10,
        filters: dict[str, Any] | None = None,
        retries: int = 1,
    ) -> dict:
        """Run the engine's native search and return its parsed JSON payload."""
        args = _search_args(query, project, all_projects, page_size, filters)
        result = await self.call_tool("search_notes", args, retries=retries)
        if _is_error(result):
            raise BMError(_text_of(result) or "search failed", kind="engine")
        text = _text_of(result)
        return json.loads(text) if text else {}

    async def search(self, query: str | None, **kwargs: Any) -> list[dict[str, Any]]:
        payload = await self.search_payload(query, **kwargs)
        return normalize_results(payload)
