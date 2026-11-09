#!/usr/bin/env bash
# Re-record the profile loader GIF from the live portfolio boot loader.
#
#   ./tools/record-loader.sh [url] [output.gif]
#
# Defaults: http://localhost:5173/?boot=1  ->  loader.gif
# Requires: node 22+, Chrome/Chromium, ffmpeg, and the portfolio dev server up.
set -euo pipefail

URL="${1:-${PORTFOLIO_URL:-http://localhost:5173/?boot=1}}"
OUT="${2:-loader.gif}"
FRAMES="$(mktemp -d)"
trap 'rm -rf "$FRAMES"' EXIT

# The loader only runs on a first visit; ?boot=1 forces it every time.
case "$URL" in
  *boot=*) ;;
  *) URL="${URL}${URL#*\?}" ;;
esac

echo "→ recording $URL"
node "$(dirname "$0")/record-loader.mjs" "$URL" "$FRAMES" "${DURATION_MS:-5200}"

count=$(find "$FRAMES" -name 'frame_*.png' | wc -l | tr -d ' ')
if [ "$count" -lt 40 ]; then
  echo "ERROR: only $count frames captured - is the site running?" >&2
  exit 1
fi

# Trim the pre-animation dark frames and the fade into the site (END_FRAME
# must stop before the overlay lifts, or the page shows through), then encode.
START_FRAME="${START_FRAME:-6}"
END_FRAME="${END_FRAME:-248}"

echo "→ encoding $OUT (frames $START_FRAME..$END_FRAME of $count)"
# trim (not -start_number/-frames:v) so the input frame numbers are exact
ffmpeg -y -loglevel error \
  -framerate 49 -i "$FRAMES/frame_%04d.png" \
  -vf "trim=start_frame=$START_FRAME:end_frame=$END_FRAME,setpts=PTS-STARTPTS,crop=1000:420:50:50,fps=18,scale=820:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 "$OUT"

ls -lh "$OUT"
