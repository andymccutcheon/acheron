#!/usr/bin/env bash
# Start the Basic Memory HTTP MCP service that Acheron talks to.
# Keep it running in a terminal, or use install-launchd.sh for a permanent setup.
# Override BM_BIN to point at a specific install; defaults to `bm` on PATH.
set -euo pipefail

BM_BIN="${BM_BIN:-$(command -v bm || true)}"
if [ -z "$BM_BIN" ]; then
  echo "bm not found on PATH; set BM_BIN=/path/to/bm" >&2
  exit 1
fi
PORT="${BM_PORT:-8765}"

exec "$BM_BIN" mcp --transport streamable-http --host 127.0.0.1 --port "$PORT"
