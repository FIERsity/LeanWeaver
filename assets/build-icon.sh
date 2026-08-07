#!/usr/bin/env bash
# Rasterise assets/icon.svg into the extension icon.
#
# The SVG is the single source of truth. Rendering uses headless Chrome because it
# is the only SVG rasteriser we can rely on being present on macOS (no librsvg /
# ImageMagick / cairosvg dependency).
#
# Usage:  ./assets/build-icon.sh
set -euo pipefail

ASSETS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$ASSETS/.." && pwd)"
SVG="$ASSETS/icon.svg"

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [[ ! -x "$CHROME" ]]; then
  echo "error: Chrome not found at '$CHROME' (override with CHROME=/path/to/chrome)" >&2
  exit 1
fi

render() {  # render <output> <device-scale-factor>
  "$CHROME" --headless --disable-gpu \
    --force-device-scale-factor="$2" \
    --default-background-color=00000000 \
    --window-size=256,256 \
    --screenshot="$1" \
    "file://$SVG" >/dev/null 2>&1
  [[ -s "$1" ]] || { echo "error: render failed for $1" >&2; exit 1; }
}

render "$ASSETS/icon-256.png" 1
render "$ASSETS/icon-128.png" 0.5

# The extension ships the 256px variant: it satisfies the marketplace minimum of
# 128x128 and stays crisp on HiDPI displays.
cp "$ASSETS/icon-256.png" "$REPO/vscode-extension/icon.png"

echo "built:"
for f in "$ASSETS/icon-256.png" "$ASSETS/icon-128.png" "$REPO/vscode-extension/icon.png"; do
  printf '  %s  %s\n' "$(sips -g pixelWidth -g pixelHeight "$f" | awk '/pixelWidth/{w=$2}/pixelHeight/{h=$2}END{printf "%sx%s", w, h}')" "${f#$REPO/}"
done
