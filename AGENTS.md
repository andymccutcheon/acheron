# Acheron — agent orientation

**What this is.** The single agent-facing MCP server over a markdown knowledge base: Basic Memory
is the storage plane (canonical markdown + local index + HTTP MCP on port 8765); `context_search`
re-ranks its search results with an optional System One decision model (Inception's Mercury
Decide by default; Perplexity Decider and TypeSafe's Jev as presets; `custom` for any endpoint
that speaks the same API), and every other engine tool is proxied under its original
name — `search_notes` is folded in and hidden. `README.md` carries the architecture, tool policy,
configuration, and the benchmark.

**Durable references.**

- Engine service on macOS: `local.basic-memory-http` via `scripts/install-launchd.sh` (README
  "Service" has restart/remove commands).
- Benchmark: `eval/demo/` is the synthetic corpus with labels; run it with `eval/benchmark.py`.
- Evaluation caveats: 16 questions, hand labels; Mercury's free tier allows 20 requests/minute,
  so run benchmarks with `--delay 3.2`.
- Keys: set `OPENROUTER_API_KEY` for the OpenRouter presets, or `ACHERON_DECISIONS_KEY` for a
  `custom` endpoint (none for a local server). The OpenRouter key is never sent to another host.
  `provider: none` returns native order.
- Ranker ladder and the evidence behind it: README "Choosing a ranker" and
  `.agent/briefs/2026-10-12-flexible-reranker.md`.
