# Acheron — agent orientation

**What this is.** The single agent-facing MCP server over a markdown knowledge base: Basic Memory
is the storage plane (canonical markdown + local index + HTTP MCP on port 8765); `context_search`
re-ranks its search results with a System One decision model (Inception's Mercury Decide by
default, TypeSafe's Jev behind a flag), and every other engine tool is proxied under its original
name — `search_notes` is folded in and hidden. `README.md` carries the architecture, tool policy,
configuration, and the benchmark.

**Durable references.**

- Engine service on macOS: `local.basic-memory-http` via `scripts/install-launchd.sh` (README
  "Service" has restart/remove commands).
- Benchmark: `eval/demo/` is the synthetic corpus with labels; run it with `eval/benchmark.py`.
- Evaluation caveats: 16 questions, hand labels; Mercury's free tier allows 20 requests/minute,
  so run benchmarks with `--delay 3.2`.
- Keys: set `OPENROUTER_API_KEY` for reranking; `provider: none` runs fully offline.
