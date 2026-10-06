#!/usr/bin/env bash
# Rebuild an explainer (product-dark, main scenario only) and patch it to autoplay.
# Usage: build-explainer.sh [scene-basename]   (default: context-search-explainer)
# Requires the visual-explainer skill; override its location with VISUAL_EXPLAINER_SKILL.
set -euo pipefail
cd "$(dirname "$0")"
SKILL="${VISUAL_EXPLAINER_SKILL:-$HOME/.agents/skills/visual-explainer}"
SCENE="${1:-context-search-explainer}"
HTML="$SCENE-product-dark.html"

python3 "$SKILL/scripts/build.py" "$SCENE.scene.js" --theme product-dark

python3 - "$HTML" <<'PY'
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = 'if(qs.has("autoplay")){ render(0); setPlay(true); }'
assert s.count(old) == 1, "autoplay hook not found; the core library may have changed"
open(p, "w", encoding="utf-8").write(s.replace(old, 'if(true){ render(0); setPlay(true); }'))
print("autoplay enabled")
PY

echo "built $HTML"
echo "export the README GIF with: bash $SKILL/scripts/run.sh render.py $HTML --gif"
