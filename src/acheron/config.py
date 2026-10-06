from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

PROVIDERS: dict[str, str | None] = {
    "mercury": "inception/mercury-decide:free",
    "jev": "typesafe/jev-1.13",
    "none": None,
}

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
    openrouter_key: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        provider = os.environ.get("ACHERON_PROVIDER", "mercury").lower()
        if provider not in PROVIDERS:
            raise ValueError(
                f"ACHERON_PROVIDER must be one of {sorted(PROVIDERS)}, got {provider!r}"
            )
        model = os.environ.get("ACHERON_MODEL") or PROVIDERS[provider]
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
            candidates=int(os.environ.get("ACHERON_CANDIDATES", "10")),
            limit=int(os.environ.get("ACHERON_LIMIT", "5")),
            rrf_k=int(os.environ.get("ACHERON_RRF_K", "60")),
            ranking=ranking,
            openrouter_key=openrouter_key(),
        )
