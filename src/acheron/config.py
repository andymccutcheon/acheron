from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

OPENROUTER_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
OPENROUTER_HOST = "openrouter.ai"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

# Presets are decision models served through OpenRouter. `custom` points at any other
# endpoint that speaks the same API (a vendor's direct endpoint or a local server) and
# takes its URL and model from the environment; `none` disables reranking.
PRESETS: dict[str, str] = {
    "mercury": "inception/mercury-decide:free",
    "perplexity": "perplexity/pplx-decider-v1.1-27b",
    "jev": "typesafe/jev-1.13",
}
CUSTOM = "custom"
PROVIDERS: dict[str, str | None] = {**PRESETS, CUSTOM: None, "none": None}

# Hard ceilings on caller-controlled rerank work (recommendations 2026-10, H1).
# Requests and environment overrides are clamped into [1, ceiling]; the ceilings sit
# well above the current defaults (5, 10) so wider-recall experiments still fit.
LIMIT_MAX = 25
CANDIDATES_MAX = 50
# Bounded rerank timeout (seconds).
TIMEOUT_MIN, TIMEOUT_MAX = 1.0, 120.0


def clamp(value: int, low: int, high: int) -> int:
    return min(max(value, low), high)


def clamp_timeout(value: float) -> float:
    return min(max(value, TIMEOUT_MIN), TIMEOUT_MAX)

def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def is_loopback(url: str) -> bool:
    return _host(url) in LOOPBACK_HOSTS


def is_openrouter(url: str) -> bool:
    return _host(url) == OPENROUTER_HOST


def validate_decisions_url(url: str) -> str:
    """Accept https anywhere and plain http only on loopback; fail fast otherwise."""
    malformed = ValueError(
        "ACHERON_DECISIONS_URL must be a full http(s) URL, "
        "for example https://host/v1/systemone"
    )
    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        port = parts.port  # raises ValueError when it is not a number in 0-65535
    except ValueError:
        raise malformed from None
    host = _host(url)
    if not host or scheme not in {"http", "https"} or port == 0:
        raise malformed
    if parts.username is not None or parts.password is not None:
        raise ValueError(
            "ACHERON_DECISIONS_URL must not carry credentials; "
            "put the key in ACHERON_DECISIONS_KEY"
        )
    if scheme == "http" and host not in LOOPBACK_HOSTS:
        raise ValueError(
            "ACHERON_DECISIONS_URL must use https unless it points at this machine "
            "(127.0.0.1, localhost or ::1)"
        )
    return url


def decision_key(
    url: str, *, openrouter_key: str | None, decisions_key: str | None
) -> str | None:
    """The key for one endpoint. A key is bound to its host: the OpenRouter key is only
    ever sent to openrouter.ai, and every other host gets ACHERON_DECISIONS_KEY or none."""
    if is_openrouter(url):
        return openrouter_key or None
    return decisions_key or None


_AUTH_PATH = Path.home() / ".local" / "share" / "opencode" / "auth.json"


def openrouter_key() -> str | None:
    """OPENROUTER_API_KEY if set, else the key OpenCode already stores."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        data = json.loads(_AUTH_PATH.read_text())
        return (data.get("openrouter") or {}).get("key") or None
    except Exception:
        return None


@dataclass(frozen=True)
class Config:
    bm_url: str = "http://127.0.0.1:8765/mcp"
    provider: str = "mercury"
    model: str | None = PROVIDERS["mercury"]
    default_project: str | None = None
    all_projects: bool = True
    candidates: int = 10
    limit: int = 5
    rrf_k: int = 60
    ranking: str = "auto"
    timeout: float = 60.0
    openrouter_key: str | None = None
    decisions_url: str = OPENROUTER_DECISIONS_URL
    decisions_key: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        provider = os.environ.get("ACHERON_PROVIDER", "mercury").lower()
        if provider not in PROVIDERS:
            raise ValueError(
                f"ACHERON_PROVIDER must be one of {sorted(PROVIDERS)}, got {provider!r}"
            )
        model = os.environ.get("ACHERON_MODEL") or PROVIDERS[provider]
        custom_url = os.environ.get("ACHERON_DECISIONS_URL") or None
        if provider == CUSTOM:
            if not custom_url:
                raise ValueError(
                    "ACHERON_PROVIDER=custom needs ACHERON_DECISIONS_URL "
                    "(the full URL of the decisions endpoint)"
                )
            if not model:
                raise ValueError(
                    "ACHERON_PROVIDER=custom needs ACHERON_MODEL (the decision model id)"
                )
        decisions_url = validate_decisions_url(custom_url or OPENROUTER_DECISIONS_URL)
        ranking = os.environ.get("ACHERON_RANKING", "auto").lower()
        if ranking not in {"auto", "model", "fuse"}:
            raise ValueError(
                f"ACHERON_RANKING must be auto, model, or fuse, got {ranking!r}"
            )
        return cls(
            bm_url=os.environ.get("ACHERON_BM_URL", "http://127.0.0.1:8765/mcp"),
            provider=provider,
            model=model,
            default_project=os.environ.get("ACHERON_DEFAULT_PROJECT") or None,
            all_projects=os.environ.get("ACHERON_ALL_PROJECTS", "true").lower()
            not in {"false", "0", "no"},
            candidates=clamp(int(os.environ.get("ACHERON_CANDIDATES", "10")), 1, CANDIDATES_MAX),
            limit=clamp(int(os.environ.get("ACHERON_LIMIT", "5")), 1, LIMIT_MAX),
            rrf_k=int(os.environ.get("ACHERON_RRF_K", "60")),
            ranking=ranking,
            timeout=clamp_timeout(float(os.environ.get("ACHERON_TIMEOUT", "60"))),
            openrouter_key=openrouter_key(),
            decisions_url=decisions_url,
            decisions_key=os.environ.get("ACHERON_DECISIONS_KEY") or None,
        )
