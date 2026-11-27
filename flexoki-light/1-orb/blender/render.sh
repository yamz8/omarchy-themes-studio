#!/bin/bash
# Renders orb.blend without opening Blender's window.
#
#   ./render.sh still     frame 1 at full size (3840x2160) -> renders/frame-0001.png
#   ./render.sh preview   the whole 8-second loop at 1280x720 -> renders/loop-preview.mp4
#
# The dot pattern is tied to pixels, so the preview is rendered at full size
# and scaled down by ffmpeg: rendering straight at 1280x720 would make the
# dots three times larger than in the still.

set -e

here="$(cd "$(dirname "$0")" && pwd)"
blend="$here/orb.blend"
out="$here/renders"
mkdir -p "$out"

case "$1" in
  still)
    blender --background "$blend" --render-output "$out/frame-####" --render-format PNG --render-frame 1
    echo "Wrote $out/frame-0001.png"
    ;;
  preview)
    frames="$(mktemp -d)"
    blender --background "$blend" --render-output "$frames/f-####" --render-format PNG --render-anim
    ffmpeg -loglevel error -y -framerate 24 -i "$frames/f-%04d.png" \
      -vf "scale=1280:720:flags=area" -c:v libx264 -pix_fmt yuv420p -crf 20 "$out/loop-preview.mp4"
    rm -rf "$frames"
    echo "Wrote $out/loop-preview.mp4"
    ;;
  *)
    echo "Usage: $0 still|preview" >&2
    exit 1
    ;;
esac
