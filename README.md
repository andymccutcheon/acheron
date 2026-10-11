# Acheron

**One MCP server for your agent's memory.** Consolidate a markdown knowledge base's tools behind
a single policy surface, and rerank retrieval so the right note comes first.

[![CI](https://github.com/andymccutcheon/acheron/actions/workflows/ci.yml/badge.svg)](https://github.com/andymccutcheon/acheron/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Basic Memory](https://github.com/basicmachines-co/basic-memory) is the storage engine: canonical
markdown, a local index, and an HTTP MCP server. Acheron sits in front of it. Agents see
**one server, one search verb, and a clean tool list**, while search results are re-ordered by a
System One decision model — with native-order fallback when the model is unavailable.

This is a reference implementation, not a product. The pattern is the point; the code is small
enough to read in an afternoon.

![The Acheron search path: a question travels from the agent through Acheron and Basic Memory to a ranked answer, including the model-failure fallback](docs/context-search-explainer-product-dark.gif)

The animation is the eleven-step search path, including the model-failure fallback. For the
interactive version — play, pause, scrub, step through — open
[`docs/context-search-explainer-product-dark.html`](docs/context-search-explainer-product-dark.html)
in a browser after cloning (GitHub serves HTML files as source).

## Why

Agents wired to a personal knowledge base hit two problems:

1. **Tool sprawl.** The engine exposes ~27 tools, including two overlapping search verbs. Every
   turn the agent must choose, and the weaker path is always selectable.
2. **Ordering is not recall.** Hybrid search finds the right notes, but hub pages, person pages,
   and passing mentions outrank the note that answers the question. On the included demo corpus,
   the expected note was first in **7/16** questions natively; after reranking, **14/16**
   (15/16 when stacked on the engine's built-in reranker).

## What it does

- **One search verb.** `context_search` absorbs the engine's filter parameters: `tags`, `status`,
  `note_types`, `entity_types`, `categories`, `metadata_filters`, `after_date`, `valid_at`,
  `valid_overlaps`, `time_kind`, `search_type`, `min_similarity`. A query is reranked; filters
  alone return native order (`ranking: "native"`).
- **Everything else proxied.** The engine's other tools are discovered at startup and re-exposed
  under their original names with schema fidelity — parameter names, JSON schemas, defaults, and
  annotations preserved. `search_notes` is folded into `context_search` and hidden; the
  ChatGPT-only connector adapters (`search`, `fetch`) are hidden too.
- **Fail-open reranking.** If the decision model errors or rate-limits, results return in native
  order with `fallback: true`. Retrieval never blocks the agent. (Basic Memory's own reranker
  deliberately fails closed with a 503 — a legitimate choice, and a different one; see
  [Design notes](#design-notes).)
- **Any model.** Mercury Decide (free tier via OpenRouter) by default; Jev behind a flag;
  `provider: none` for fully local retrieval.

![The Acheron storage path: a markdown note lands in a watched folder, is parsed into the local index, and its wikilinks become edges in a graph that queries can walk](docs/storage-explainer-product-dark.gif)

The storage story: markdown stays the source of truth; the index and the relations graph are
derived and rebuildable. The interactive version —
[`docs/storage-explainer-product-dark.html`](docs/storage-explainer-product-dark.html).

## Documentation site

The `docs/` folder is published as a static site via GitHub Actions (workflow:
`.github/workflows/docs-pages.yml`). After an operator turns on GitHub Pages for this repository
with **GitHub Actions** as the source, the operator's guide and interactive explainers will be
served from the repository's `github.io` URL. Until then, open the HTML files locally or run a
static server from `docs/`.

## Quickstart

Prereqs: Python 3.12+, [Basic Memory](https://github.com/basicmachines-co/basic-memory) with a
project of markdown notes, and — for reranking — an OpenRouter key (the Mercury tier is free).
Without a key the server still works and returns native order.

```sh
uv sync
scripts/start-bm-http.sh     # engine HTTP MCP service on port 8765; or scripts/install-launchd.sh
uv run acheron        # the one agent-facing server (stdio)
```

Wire it into an MCP client:

OpenCode (`~/.config/opencode/opencode.jsonc`):

```jsonc
"acheron": {
  "type": "local",
  "command": ["uv", "run", "--directory", "/path/to/acheron", "acheron"],
  "enabled": true
}
```

Claude Code:

```sh
claude mcp add --scope user acheron -- /path/to/acheron/.venv/bin/acheron
```

Do **not** also configure the storage engine's own MCP entry — this server proxies it.

## Reproduce the benchmark

The repo ships a synthetic corpus (23 notes for a fictional photo-sync project) and 16 labeled
questions. Replay mode needs no engine and no index — just an OpenRouter key:

```sh
# no engine needed: rerank the recorded candidate lists
uv run python eval/benchmark.py --replay eval/demo/candidates.json --provider mercury --delay 3.2

# full run: index the demo corpus first
bm project add tidepool eval/demo/notes
uv run python eval/benchmark.py --questions eval/demo/questions.json --provider mercury --delay 3.2
```

Measured (16 questions, top-1 / top-3):

| Method | Top-1 | Top-3 |
| --- | ---: | ---: |
| Native hybrid (engine default) | 7 | 12 |
| Engine's built-in local reranker (fastembed) | 12 | 14 |
| Mercury Decide (free) | 14 | 15 |
| Mercury stacked on the built-in reranker | **15** | **16** |

Caveats, stated up front: 16 questions, hand labels, one synthetic corpus — differences of 1–3
questions are within noise. The engine's built-in reranker is strong and free; this project's
value is not "better ranking." It is the single surface, the fail-open contract, portability
across models, and evidence you can rerun. Raw results in `eval/demo/`.

## Tools

One server, one search verb, plus the full engine toolset:

- **`context_search`** — the only search. Query → reranked; filters only → native passthrough.
- **Everything else** — proxied under the engine's original names: `read_note`, `write_note`,
  `edit_note`, `delete_note`, `move_note`, `build_context`, `recent_activity`, `list_directory`,
  `grep`, `find`, `ls`, `cat`, `tail`, `man`, the schema tools, and so on. Write-tool annotations
  (for example `destructiveHint`) are preserved.
- **Hidden** — `search_notes` (folded into `context_search`), `search`, `fetch`.

## Memory skill

`skills/acheron-memory/` is a portable agent skill for the write side: it seeds a corpus from
existing folders, captures durable facts mid-session, and wraps sessions into distilled, linked
notes. It encodes the discipline that makes search and the relations graph pay off — search
before write, verify every link, distil before saving — and ships with `corpus_scan.py`, a
dependency-free inventory and broken-link audit.

```sh
cp -r skills/acheron-memory ~/.claude/skills/     # or your agent's skills directory
```

The packaged `skills/acheron-memory.zip` suits clients that accept skill uploads; otherwise point
any agent at `skills/acheron-memory/SKILL.md`. It uses the MCP tools when connected and plain
markdown files when not.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ACHERON_BM_URL` | `http://127.0.0.1:8765/mcp` | Engine HTTP MCP endpoint |
| `ACHERON_PROVIDER` | `mercury` | `mercury`, `jev`, or `none` |
| `ACHERON_MODEL` | provider default | Override the decision model id |
| `ACHERON_DEFAULT_PROJECT` | none | Project scope when the caller passes none |
| `ACHERON_ALL_PROJECTS` | `true` | Search every project when unscoped |
| `ACHERON_CANDIDATES` | `10` | Native candidates to rerank (clamped to 1–50) |
| `ACHERON_LIMIT` | `5` | Results returned (clamped to 1–25) |
| `ACHERON_TIMEOUT` | `60` | Rerank call timeout, seconds (clamped to 1–120) |
| `ACHERON_RANKING` | `auto` | `auto` (Mercury→model, JEV→fuse), `model`, or `fuse` |
| `ACHERON_RRF_K` | `60` | RRF smoothing constant |

Keys: `OPENROUTER_API_KEY` if set, otherwise the key OpenCode already stores in
`~/.local/share/opencode/auth.json` is reused. Nothing else is needed.

## Service (macOS)

`scripts/install-launchd.sh` generates a LaunchAgent (`local.basic-memory-http`) for the engine's
HTTP MCP service: starts at login, kept alive, logs to `~/Library/Logs/basic-memory-http.log`.
Launching through `/bin/bash` matters on macOS: scheduled jobs do not inherit Full Disk Access,
so a process that must read files under `~/Documents` has to go through a shell that has it.

```sh
launchctl kickstart -k gui/$(id -u)/local.basic-memory-http   # restart
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/local.basic-memory-http.plist  # remove
```

## Design notes

- **Fail-open vs fail-closed.** The engine treats an enabled reranker as part of the ranking
  contract and returns 503 when it fails. Acheron treats ranking as best-effort: a model
  failure degrades ordering, never availability. Both are defensible; pick per your workload.
- **Bounded rerank work.** Per-request `limit` and `candidates` and every environment override
  are clamped into hard ceilings (25 results, 50 candidates), so one call cannot inflate latency,
  payload size, or provider usage. Candidate text reaches the reranker as untrusted evidence, and
  transport or invalid-body failures from the decision API fall open like any ranking failure.
- **Fold, don't rename.** Proxied tools keep the engine's names — a rename map costs
  maintenance and fights upstream docs. Only the duplicate search verb is folded, because two
  search tools is a per-turn decision tax.
- **Schema fidelity mechanics.** Proxied parameter schemas are pinned from the engine's own tool
  definitions via pydantic `WithJsonSchema`; validation stays permissive so bad input surfaces as
  the engine's error, not a local one. `CallToolResult` objects are forwarded verbatim, preserving
  error shapes and structured content.
- **Startup discovery.** Tools are discovered when the server starts. If the engine was down then,
  restart acheron to pick up the proxied tools; `context_search` still works meanwhile.

## Development

```sh
uv run pytest                     # 30 tests
uv run python eval/demo/build_corpus.py   # regenerate the synthetic corpus
```

## Status

v0.2.1, MIT. Reference implementation: no support promise, no maintenance guarantee. Issues and
pull requests are welcome best-effort. The demo corpus is synthetic; no personal data ships here.
