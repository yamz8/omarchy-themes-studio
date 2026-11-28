#!/bin/bash
# Renders the Loop or the Intro scene of a base file without opening Blender's window, and
# encodes it the way Omarchy takes it (docs/fixed-ground.md).
#
#   ./render.sh loop  [file.blend]   -> out/loop.mp4   (default file: out/base.blend)
#   ./render.sh intro [file.blend]   -> out/intro.mp4
#
# Both: H.264 High at level 5.1 (older Intel laptops decode above it with damage), 24 fps,
# 3160 x 2280, yuv420p, bt709 colour tags, frame count in the header.
# The loop also gets exactly one keyframe and no B-frames, as the loops repository checks.
#
# CRF 16 at the slowest preset is a safe start. Before a pull request, a reviewer will ask for the
# highest CRF that still holds VMAF 96 on average against the frames (see fixed-ground.md).

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
kind="${1:-}"
blend="$(realpath "${2:-$here/out/base.blend}")"
crf="${CRF:-16}"

case "$kind" in
  loop)  scene=Loop;  gop=(-x264-params "keyint=infinite:min-keyint=1:scenecut=0" -bf 0) ;;
  intro) scene=Intro; gop=() ;;
  *) echo "Usage: $0 loop|intro [file.blend]" >&2; exit 1 ;;
esac

frames="$here/out/$kind/frames"
rm -rf "$frames"; mkdir -p "$frames"
blender --background "$blend" --scene "$scene" --render-output "$frames/f-####" --render-format PNG --render-anim

ffmpeg -loglevel error -y -framerate 24 -i "$frames/f-%04d.png" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -preset veryslow -crf "$crf" -profile:v high -level:v 5.1 "${gop[@]}" \
  -movflags +faststart -an "$here/out/$kind.mp4"

echo "Wrote $here/out/$kind.mp4 from $(ls "$frames" | wc -l) frames of $blend"
ffprobe -v error -select_streams v -show_entries stream=width,height,nb_frames,level,color_space -of compact "$here/out/$kind.mp4"
