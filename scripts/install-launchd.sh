#!/usr/bin/env bash
# Install (or refresh) the Basic Memory HTTP MCP service under launchd (macOS).
# Generates a LaunchAgent for the current user from a neutral template.
# Override BM_BIN (default: `bm` on PATH), LABEL, or BM_PORT as needed.
set -euo pipefail
cd "$(dirname "$0")"

BM_BIN="${BM_BIN:-$(command -v bm || true)}"
if [ -z "$BM_BIN" ]; then
  echo "bm not found on PATH; set BM_BIN=/path/to/bm" >&2
  exit 1
fi
LABEL="${LABEL:-local.basic-memory-http}"
PORT="${BM_PORT:-8765}"
UID_NUM="$(id -u)"
LOG="$HOME/Library/Logs/basic-memory-http.log"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
SCRIPT="$PWD/start-bm-http.sh"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$DEST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$SCRIPT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>15</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>BM_BIN</key>
    <string>$BM_BIN</string>
    <key>BM_PORT</key>
    <string>$PORT</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG</string>
  <key>StandardErrorPath</key>
  <string>$LOG</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$UID_NUM" "$DEST" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$DEST"
echo "installed $LABEL -> $DEST"
launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null | grep -E "state = |pid = " | head -4 || true
