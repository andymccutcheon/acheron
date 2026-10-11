# Acheron baseline dossier (code-grounded)

Generated: 2026-10-10. Repository: `/Users/andymccutcheon/Documents/GitHub/acheron`. Read-only inspection; no tests executed in-repo.

---

## 1. Plain-language summary

Acheron is a **stdio MCP server** that sits in front of [Basic Memory](https://github.com/basicmachines-co/basic-memory) (markdown storage, local index, hybrid search) exposed as an HTTP MCP service (`README.md:9-12`, `scripts/start-bm-http.sh:14`). Agents get **one search tool**, `context_search`, which calls the engine’s `search_notes` under the hood, optionally **re-orders** candidates via OpenRouter’s **Decisions API** (Mercury Decide or Jev models), and **proxies** every other engine tool at startup with schemas copied from the engine (`server.py:112-127`, `server.py:130-287`, `bm.py:137`). Filter-only searches skip reranking and return native engine JSON (`server.py:199-212`). Reranking **fails open**: missing API key or model errors yield native order with `fallback: true` (`server.py:236-252`, `README.md:45-48`). The Python package is small (~6 modules under `src/acheron/`), depends only on `mcp` and `httpx` (`pyproject.toml:17-20`), and ships a synthetic eval corpus plus `eval/benchmark.py` (`eval/benchmark.py:1-21`). Extension is mostly **environment variables** and the hard-coded `PROVIDERS` map (`config.py:8-67`); there is no plugin loader. A separate **acheron-memory** skill documents write-side workflows and a stdlib `corpus_scan.py` helper (`skills/acheron-memory/SKILL.md:1-8`).

---

## 2. Architecture detail

### 2.1 Module responsibilities

| Module | Role | Key symbols (path:line) |
|--------|------|-------------------------|
| `server.py` | FastMCP app, `context_search`, proxy registration, CLI `main` | `FastMCP("acheron")` `server.py:35`; `visible_tools` `server.py:67-68`; `proxy_fn` `server.py:71-97`; `_forward` `server.py:100-109`; `register_proxies` `server.py:112-127`; `context_search` `server.py:150-287`; `main` `server.py:290-298` |
| `bm.py` | MCP client to Basic Memory HTTP endpoint; normalize search results | `BMError` `bm.py:15-20`; `normalize_results` `bm.py:27-42`; `BMClient.call_tool` `bm.py:94-106`; `BMClient.list_tools` `bm.py:108-123`; `BMClient.search_payload` / `search` `bm.py:125-145` |
| `config.py` | Env-based settings and OpenRouter key resolution | `PROVIDERS` `config.py:8-12`; `openrouter_key` `config.py:17-26`; `Config` / `from_env` `config.py:29-67` |
| `decisions.py` | OpenRouter Decisions API scoring | `RUBRIC` `decisions.py:9-14`; `build_payload` `decisions.py:23-40`; `parse_scores` `decisions.py:43-50`; `score_candidates` `decisions.py:53-79` |
| `ranking.py` | Order fusion / model-only ranking | `rank_by_model` `ranking.py:19-40`; `fuse` (RRF) `ranking.py:43-73` |
| `__main__.py` | Entry shim | `main` `__main__.py:1-4` |
| `__init__.py` | Package version string (stale vs pyproject) | `__version__ = "0.1.0"` `__init__.py:1` |

### 2.2 `context_search` end-to-end flow

1. **Load config** — `Config.from_env()`; per-call overrides for `limit`, `candidates`, `project`, `provider` (`server.py:169-173`, `config.py:43-67`).
2. **Validate input** — Require non-empty `query` or at least one filter; else JSON error (`server.py:192-195`).
3. **Filter-only branch** — `bm.search_payload(None, …)` → engine `search_notes` with filters only; attach `ranking: "native"`, `mode: "filter"` (`server.py:199-212`, `bm.py:136-141`).
4. **Query branch** — `bm.search(query, …)` → `search_notes` with `page_size=max(candidates, limit)` (`server.py:214-221`, `bm.py:143-145`).
5. **Candidate slice** — `candidates_list = raw[:candidates]` (`server.py:228`).
6. **Decision model (optional)** — Resolve provider/model (`server.py:230-231`, `config.py:8-12`). If `model` is non-`None` and key present, `score_candidates` POST to `https://openrouter.ai/api/alpha/decisions` (`server.py:236-252`, `decisions.py:7`, `decisions.py:53-79`). On missing key or `DecisionsError`, set `fallback=True` and leave scores unset (`server.py:237-252`).
7. **Ranking mode** — `ACHERON_RANKING`: `auto` maps mercury→`model`, jev→`fuse` (`server.py:254-256`). Apply `rank_by_model` or `fuse` (`server.py:257-260`, `ranking.py:19-73`).
8. **Response** — JSON with snippets truncated to 600 chars, timing, per-result ranks/scores (`server.py:263-287`).

### 2.3 Wrappers and dependencies

- **Storage & retrieval engine:** Basic Memory, contacted via streamable HTTP MCP (`bm.py:79-86`, `bm.py:99-103`). Search uses tool name **`search_notes`** (`bm.py:137`). Embeddings/hybrid search and any **engine-side reranker (e.g. fastembed)** live in Basic Memory, not in Acheron source; Acheron only documents benchmark comparisons in README and committed `eval/demo/results-*.json` (`README.md:109-111`, `eval/demo/results-bm-fastembed.json:1-15`).
- **Reranker (Acheron layer):** OpenRouter **Decisions API** with models `inception/mercury-decide:free` and `typesafe/jev-1.13` (`config.py:8-11`, `decisions.py:7-8`). Not a local embedding reranker in this repo.
- **Runtime Python deps (direct):** `mcp>=1.0,<2`, `httpx>=0.27` (`pyproject.toml:17-20`). `server.py` also imports `pydantic.WithJsonSchema` (`server.py:22`) — supplied transitively via `mcp`, not declared in `pyproject.toml`.
- **External process:** `bm mcp --transport streamable-http` on `127.0.0.1:8765` by default (`scripts/start-bm-http.sh:12-14`, `config.py:31`).

### 2.4 MCP exposure

- **Transport:** stdio via `mcp.run()` in `main()` (`server.py:298`).
- **Tools defined in Acheron code (static):**
  - **`context_search`** — `@mcp.tool(name="context_search", …)` (`server.py:130-149`).
- **Tools registered dynamically at startup:** For each engine tool from `bm.list_tools()` except names in `HIDDEN_TOOLS`, Acheron `add_tool(proxy_fn(...), name=tool.name, …)` (`server.py:33`, `server.py:112-125`, `bm.py:108-118`). If discovery fails, startup logs a warning and only `context_search` is guaranteed (`server.py:295-297`, `README.md:186-187`).
- **Hidden from agents (folded or connector-only):** `search_notes`, `search`, `fetch` (`server.py:33`, `server.py:67-68`, `README.md:43-44`, `README.md:127`).
- **Proxied tool inventory:** **Not fixed in source.** README examples include `read_note`, `write_note`, `edit_note`, `delete_note`, `move_note`, `build_context`, `recent_activity`, `list_directory`, `grep`, `find`, `ls`, `cat`, `tail`, `man`, schema tools (`README.md:123-126`). `.agent/state.md` records an operational count of 24 proxied tools when 27 engine tools were discovered (`state.md:28-30`) — that count is environment-specific, not asserted in code.

### 2.5 Storage model

Canonical **markdown on disk** and a **derived index** are owned by Basic Memory (`README.md:54-56`, `skills/acheron-memory/SKILL.md:8`). Acheron does not read the filesystem directly for search.

### 2.6 Configuration surface

| Variable | Default | Code |
|----------|---------|------|
| `ACHERON_BM_URL` | `http://127.0.0.1:8765/mcp` | `config.py:31`, `config.py:56` |
| `ACHERON_PROVIDER` | `mercury` (`mercury` \| `jev` \| `none`) | `config.py:8-12`, `config.py:44-48` |
| `ACHERON_MODEL` | provider default from `PROVIDERS` | `config.py:49` |
| `ACHERON_DEFAULT_PROJECT` | none | `config.py:34`, `config.py:59` |
| `ACHERON_ALL_PROJECTS` | `true` | `config.py:35`, `config.py:60-61` |
| `ACHERON_CANDIDATES` | `10` | `config.py:36`, `config.py:62` |
| `ACHERON_LIMIT` | `5` | `config.py:37`, `config.py:63` |
| `ACHERON_RANKING` | `auto` (`auto` \| `model` \| `fuse`) | `config.py:39`, `config.py:50-54`, `config.py:65` |
| `ACHERON_RRF_K` | `60` | `config.py:38`, `config.py:64` |
| `OPENROUTER_API_KEY` or OpenCode `~/.local/share/opencode/auth.json` | — | `config.py:17-26`, `README.md:159-160` |

Per-request overrides on `context_search`: `query`, `project`, `limit`, `candidates`, `provider`, and twelve engine filter fields (`server.py:150-167`).

---

## 3. Extension points (in code) vs hard-coded behavior

### 3.1 Seams that exist

- **Provider → model map:** `PROVIDERS` dict; extend by editing source (`config.py:8-12`).
- **Env-driven `Config`:** all `ACHERON_*` keys above (`config.py:43-67`).
- **Ranking strategy:** `ACHERON_RANKING` + auto provider mapping (`server.py:254-260`).
- **RRF constant:** `ACHERON_RRF_K` passed to `fuse(..., k=cfg.rrf_k)` (`server.py:260`, `ranking.py:46`).
- **Visibility policy:** `HIDDEN_TOOLS` frozenset (`server.py:33`, `server.py:67-68`).
- **Proxy schema mirroring:** `proxy_fn` builds kwargs from engine `inputSchema` (`server.py:71-97`).
- **Decisions rubric:** four criteria strings in `RUBRIC` (`decisions.py:9-14`) — editable in source only.

### 3.2 No seam (hard-coded)

- **Decisions endpoint URL** `DECISIONS_URL` (`decisions.py:7`).
- **Snippet sizes** 500 (payload) / 600 (response) (`decisions.py:16`, `decisions.py:26`, `server.py:276`).
- **Engine-down user message** `ENGINE_DOWN` (`server.py:31`, `server.py:61-64`).
- **Retries:** BM `call_tool` retries=1 (`bm.py:94`); decisions retry on 429/5xx once (`decisions.py:74-77`).
- **No dynamic plugin/registry** for ranking, storage, or auth beyond env vars.
- **Single folded search implementation** always targets `search_notes` (`bm.py:137`); no alternate engine tool name.
- **`context_search` description text** names “Andy’s context library” (`server.py:133-141`).

---

## 4. Maturity

### 4.1 Tests

- **Count:** 24 test functions across 4 files (`tests/test_server.py:11`, `tests/test_decisions.py:5`, `tests/test_ranking.py:5`, `tests/test_bm_parse.py:3`; verified by ripgrep count).
- **Coverage themes:**
  - Tool visibility and proxy schema/forwarding (`tests/test_server.py:29-81`, `tests/test_server.py:189-193`).
  - `context_search` filter-only, query+fallback without key, filters on query, validation, BM errors (`tests/test_server.py:125-178`).
  - Result normalization and MCP result shape helpers (`tests/test_bm_parse.py:6-43`).
  - RRF / model ranking (`tests/test_ranking.py:8-46`).
  - Decisions payload, parse, HTTP mock including rate-limit retry (`tests/test_decisions.py:15-100`).
- **Gap (by inspection):** No test exercises successful rerank with mocked scores end-to-end through `context_search` (only fallback path in `test_query_search_still_reranks_with_fallback`, `tests/test_server.py:139-149`).

### 4.2 Eval harness

- **`eval/benchmark.py`:** Engine mode runs `BMClient.search` then optional `score_candidates` + `fuse`; replay mode uses `eval/demo/candidates.json` (`eval/benchmark.py:68-91`, `eval/benchmark.py:116-160`). Default questions path `eval/questions.json` (`eval/benchmark.py:81`) — **gitignored** (`.gitignore:6-8`).
- **Public demo:** 16 questions in `eval/demo/questions.json` (`eval/demo/questions.json:1-17`); 23 markdown notes (`eval/demo/build_corpus.py:12`, corpus file count verified on disk).
- **Recorded results (tracked):**
  - `eval/demo/results-reranker-off.json` — native top1 **7**/16, mercury top1 **14**/16 (`eval/demo/results-reranker-off.json:3-14`).
  - `eval/demo/results-bm-fastembed.json` — native top1 **12**/16, mercury top1 **15**/16 (`eval/demo/results-bm-fastembed.json:3-14`).
- README publishes the same demo table (native 7, fastembed 12, Mercury 14, stacked 15) (`README.md:104-111`).
- **Local-only:** `eval/results-*.json` gitignored (`.gitignore:8`); `state.md` references 25-question private set (`state.md:122-123`).

### 4.3 Docs

- **README:** architecture, quickstart, benchmark, tools policy, config, design notes (`README.md:1-199`).
- **AGENTS.md:** short orientation (`AGENTS.md:1-17`).
- **`docs/guide.html`:** operator guide (committed; README does not link it — `state.md:116-117`).
- **`docs/`:** HTML/GIF explainers for search and storage paths (`README.md:19-22`, `README.md:54-56`).
- **`skills/acheron-memory/`:** agent skill + `corpus_scan.py` (`skills/acheron-memory/SKILL.md`).

### 4.4 Git activity

- **First commit:** 2026-10-05 20:07:14 -0600 `c6d7978` (`git log`).
- **Latest commit:** 2026-10-08 08:13:56 -0600 `d68262c` (`git log`).
- **Commit count:** 2 (`git rev-list --count HEAD`).
- **Tracked files:** 63 (`git ls-files`).

### 4.5 Version and license

- **Package version:** `0.2.0` (`pyproject.toml:3`, `README.md:198`).
- **`__init__.__version__`:** `0.1.0` (`__init__.py:1`) — inconsistent with pyproject.
- **License:** MIT (`LICENSE:1`, `pyproject.toml:7`, `README.md:198`).
- **Status:** README labels v0.2.0 reference implementation, no support guarantee (`README.md:197-199`); PyPI classifier Alpha (`pyproject.toml:11`).

### 4.6 Dependencies (from `pyproject.toml`)

| Package | Constraint |
|---------|------------|
| `mcp` | `>=1.0,<2` |
| `httpx` | `>=0.27` |
| `pytest` | `>=8.0` (dev) |
| `pytest-asyncio` | `>=0.24` (dev) |

Locked versions in `uv.lock` include e.g. `acheron 0.2.0`, `httpx`, `mcp` (`uv.lock:9-16`).

---

## 5. Known gaps and limitations (quoted)

**Product / design (README)**

> "This is a reference implementation, not a product." (`README.md:14-15`)

> "Caveats, stated up front: 16 questions, hand labels, one synthetic corpus — differences of 1–3 questions are within noise." (`README.md:113-114`)

> "Startup discovery. Tools are discovered when the server starts. If the engine was down then, restart acheron to pick up the proxied tools; `context_search` still works meanwhile." (`README.md:186-187`)

**Eval / rate limits (AGENTS.md)**

> "Evaluation caveats: 16 questions, hand labels; Mercury's free tier allows 20 requests/minute, so run benchmarks with `--delay 3.2`." (`AGENTS.md:15-16`)

**Open work and operational notes (`.agent/state.md` — local, gitignored)**

> "Publish (prepared, awaiting Andy)." (`state.md:110-115`)

> "Operator's guide (`docs/guide.html`). Decide whether it ships publicly (linked from the README) or stays the local operator's manual; it is committed but currently unlinked." (`state.md:116-117`)

> "Expand and rerun the eval set. 25 questions today; raw runs in `eval/`." (`state.md:122-123`)

> "PyPI name `acheron` is taken … a future PyPI distribution would use `acheron-mcp`." (`state.md:77-81`)

**Code-implied limitations**

- Without OpenRouter key, query search never calls the decision model (`server.py:237-239`).
- `provider: none` sets `model` to `None` (`config.py:11`); ranking stays native (`server.py:236`, `ranking.py:50-51`).
- No `TODO`/`FIXME` markers in tracked Python under `src/` (repository search returned none).

---

## 6. Could not determine (without running services)

- **Exact live proxied tool list and JSON schemas** for a given Basic Memory version — depends on `list_tools()` at runtime (`server.py:116-118`).
- **Whether Basic Memory’s fastembed reranker is enabled** in a given deployment — not configured in Acheron code; only benchmark artifacts name it (`eval/demo/results-bm-fastembed.json`).
- **CI pass/fail on latest commit** — workflow exists (`/.github/workflows/ci.yml:1-19`) but was not executed in this session.
- **Contents of gitignored `eval/questions.json` and `eval/results-*.json`** on disk — present locally but excluded from published tree (`.gitignore:6-8`); `state.md` cites aggregate scores (`state.md:122-123`) without reproducing rows in repo.

---

*End of dossier.*
