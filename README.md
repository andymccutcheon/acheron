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

![The Acheron search path: a question travels from the agent through Acheron and Basic Memory to a ranked answer, including the model-failure fallback](docs/context-search-explainer-pattern-dark-poster.png)

The animation is the eleven-step search path, including the model-failure fallback. For the
interactive version — play, pause, scrub, step through — open
[`context-search-explainer-pattern-dark.html`](https://andymccutcheon.github.io/acheron/context-search-explainer-pattern-dark.html).

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
- **Any decision model, any endpoint.** Mercury Decide (free tier via OpenRouter) by default;
  Perplexity Decider and Jev as presets; `custom` for any endpoint that speaks the same API,
  including a local server; `provider: none` for native order. No model is required.

![The Acheron storage path: a markdown note lands in a watched folder, is parsed into the local index, and its wikilinks become edges in a graph that queries can walk](docs/storage-explainer-pattern-dark-poster.png)

The storage story: markdown stays the source of truth; the index and the relations graph are
derived and rebuildable. The interactive version —
[`storage-explainer-pattern-dark.html`](https://andymccutcheon.github.io/acheron/storage-explainer-pattern-dark.html).

## Documentation site

The `docs/` folder can be published as a static site via GitHub Actions (workflow:
`.github/workflows/docs-pages.yml`). The workflow copies an explicit allowlist into a staging
directory before deploy. It publishes `index.html`, `guide.html`, `.nojekyll`, and the two dark
interactive explainers. The explainers are served at
`https://andymccutcheon.github.io/acheron/context-search-explainer-pattern-dark.html` and
`https://andymccutcheon.github.io/acheron/storage-explainer-pattern-dark.html`; other files under
`docs/` remain repository-only unless they are added to the allowlist.

## Quickstart

Prereqs: Python 3.12+ and [Basic Memory](https://github.com/basicmachines-co/basic-memory) with
a project of markdown notes. Nothing else is required: without a key the server works and
returns native order. See [Choosing a ranker](#choosing-a-ranker) for the optional upgrades.

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

## Choosing a ranker

Every rung is optional, and each one works without the ones below it. Scores are "expected note
ranked first" on the 16-question demo benchmark; native order scores 7.

| Rung | What you need | Setup | Score |
| --- | --- | --- | ---: |
| 1. No key | Nothing | Set `"reranker_enabled": true` in Basic Memory's `config.json`, restart the engine | 12 |
| 2. Recommended | A free OpenRouter key | `OPENROUTER_API_KEY=...` (Mercury Decide is the default) | 14 |
| 3. Paid alternates | An OpenRouter key with credit | `ACHERON_PROVIDER=perplexity` or `ACHERON_PROVIDER=jev` | 13–14 |
| 4. Your own endpoint | Any `/v1/systemone`-compatible server | `ACHERON_PROVIDER=custom` plus URL and model (below) | depends on the model |

Rungs 1 and 2 stack: Mercury on top of the engine's reranker scored 15.

- **Rung 1 fails closed.** The engine's reranker returns an error when it fails, where
  Acheron's own reranking falls back to native order. See [Design notes](#design-notes).
- **Rung 3 is a preference, not an upgrade.** Mercury, Perplexity Decider and Jev land within
  one question of each other here, which is inside the noise. On a private 25-question set over
  real notes (not shipped), Mercury ranked the expected note first 19 times, Perplexity Decider
  20 and Jev 14, so the free default gives nothing up.
- **Rung 4** covers a vendor's direct endpoint or a local server such as llama.cpp or LM Studio
  running an open-weight decision model:

  ```sh
  ACHERON_PROVIDER=custom \
  ACHERON_DECISIONS_URL=http://127.0.0.1:9931/v1/systemone \
  ACHERON_MODEL=your-decision-model \
  uv run acheron
  ```

  Verified against llama.cpp's `llama-server` on 2026-10-12, with no key sent. Ranking quality
  depends entirely on the model you load: the smallest open-weight one tried (Kev 0.8B, 812 MB)
  scored 8, barely above native order, so a small local model is not a substitute for rung 1.
  Measure yours with `eval/benchmark.py --url ... --model ...`.

## Reproduce the benchmark

The repo ships a synthetic corpus (23 notes for a fictional photo-sync project) and 16 labeled
questions. Replay mode needs no engine and no index — just a key for the endpoint you score
against (an OpenRouter key for the presets, none for a local server):

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
| Perplexity Decider v1.1 27B | 14 | 15 |
| Jev 1.13 | 13–14 (two runs) | 15 |
| Kev 0.8B, local via llama.cpp | 8 | 12 |
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
| `ACHERON_PROVIDER` | `mercury` | `mercury`, `perplexity`, `jev`, `custom`, or `none` |
| `ACHERON_MODEL` | provider default | Decision model id; required for `custom` |
| `ACHERON_DECISIONS_URL` | OpenRouter's decisions endpoint | Full URL of the decisions endpoint; required for `custom`. Must be `https` unless it is on this machine |
| `ACHERON_DECISIONS_KEY` | none | Bearer key for a non-OpenRouter endpoint; omit for a local server |
| `ACHERON_DEFAULT_PROJECT` | none | Project scope when the caller passes none |
| `ACHERON_ALL_PROJECTS` | `true` | Search every project when unscoped |
| `ACHERON_CANDIDATES` | `10` | Native candidates to rerank (clamped to 1–50) |
| `ACHERON_LIMIT` | `5` | Results returned (clamped to 1–25) |
| `ACHERON_TIMEOUT` | `60` | Rerank call timeout, seconds (clamped to 1–120) |
| `ACHERON_RANKING` | `auto` | `auto` or `model` (order by model score), or `fuse` (blend with native order) |
| `ACHERON_RRF_K` | `60` | RRF smoothing constant |

Keys: for OpenRouter, `OPENROUTER_API_KEY` if set, otherwise the key OpenCode already stores in
`~/.local/share/opencode/auth.json` is reused. A key is bound to its host: the OpenRouter key is
only ever sent to `openrouter.ai`, and any other endpoint receives `ACHERON_DECISIONS_KEY` or no
key at all. The endpoint comes from the environment only; the per-call `provider` argument
accepts preset names and `none`, never a URL or a model id.

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
  payload size, or provider usage. A clamp that fires is disclosed, never silent: the response
  payload carries a `clamped` object (`requested` → `effective` per parameter) and the server
  logs one warning line, so an operator can cite the event. Candidate text reaches the reranker
  as untrusted evidence — guarded by a preamble before and a ruling after the text — and
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
uv run pytest                     # 86 tests
uv run python eval/demo/build_corpus.py   # regenerate the synthetic corpus
```

## Status

v0.3.0, MIT. Reference implementation: no support promise, no maintenance guarantee. Issues and
pull requests are welcome best-effort. The demo corpus is synthetic; no personal data ships here.
