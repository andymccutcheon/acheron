#!/usr/bin/env bash
# Rebuild both explainers in pattern and pattern-dark (posters, stills, MP4, steps JSON).
# Usage: ./build-explainer.sh
# Requires visual-explainer; override with VISUAL_EXPLAINER_SKILL.
# Requires ImageMagick for deterministic, size-budgeted PNG output.
set -euo pipefail
cd "$(dirname "$0")"
SKILL="${VISUAL_EXPLAINER_SKILL:-$HOME/.agents/skills/visual-explainer}"
RENDER_FLAGS=(--poster --final-still --steps-json)
SCENES=(context-search-explainer storage-explainer)
THEMES=(pattern pattern-dark)

for scene in "${SCENES[@]}"; do
  for theme in "${THEMES[@]}"; do
    python3 "$SKILL/scripts/build.py" "$scene.scene.js" --theme "$theme"
    bash "$SKILL/scripts/run.sh" render.py "$scene.scene.js" --theme "$theme" "${RENDER_FLAGS[@]}"
  done
done

command -v magick >/dev/null || {
  echo "ImageMagick (magick) is required to optimize PNG stills" >&2
  exit 1
}

for image in *-poster.png *-final.png; do
  optimized="${image%.png}.optimized.png"
  magick "$image" -strip +dither -colors 256 -define png:compression-level=9 "$optimized"
  mv "$optimized" "$image"
done

echo "built ${#SCENES[@]} scenes × ${#THEMES[@]} themes in $(pwd)"
