#!/usr/bin/python
"""Make the shapes of the Vantablack dot hands scene, and measure how the shipped loop swells its dots.

Usage: cut.py [still] [loop]

The still is two hands drawn in dots of two sizes on black. In the loop a swell passes over the
picture from left to right once a cycle: each dot grows as it passes and shrinks back, the small
ones much more than the large ones. Nothing is cut out. This writes:

  pieces/dots.png     where the dots are, with room to swell: a grey picture, white round each
                      small dot and mid grey round each large one.
  effects/swell.glsl  the scene's shader, from effects/swell.template.glsl, with how far a dot of
                      each size has grown at each moment of the swell's passing, measured from
                      the loop.

Nothing is taken from the loop but those numbers and the time the swell reaches each place.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/vantablack/backgrounds")
STILL = Path(sys.argv[1]) if len(sys.argv) > 1 else THEMES / "0-dot-hands.webp"
LOOP = Path(sys.argv[2]) if len(sys.argv) > 2 else THEMES / "loops" / "0-dot-hands.mp4"

# The band of the picture the hands are in: left, top, width, height, as shares of it. scene.jsonc says the same.
BAND = (0.0, 0.29, 1.0, 0.42)
LIT = 40      # a pixel brighter than this is part of a dot
SIZES = 60    # dots of fewer lit pixels than this are the small ones
ROOM = 4.5    # pixels of the still around a dot that its shape leaves for it to swell into
LARGE_GREY = 0.5  # how the shape marks the room round a large dot; the shader knows it too
SPAN = 24     # frames before and after the swell's middle that are measured


def main():
  still = np.asarray(Image.open(STILL).convert("L")).astype(np.float32)
  height, width = still.shape
  top, bottom = round(BAND[1] * height), round((BAND[1] + BAND[3]) * height)
  band = still[top:bottom]
  dots, count = ndi.label(band > LIT)
  each = np.arange(1, count + 1)
  area = ndi.sum(band / 255, dots, each)
  across = np.array(ndi.center_of_mass(band, dots, each))[:, 1]
  small = ndi.sum(np.ones_like(band), dots, each) < SIZES
  print(f"{count} dots in the band: {small.sum()} small, {(~small).sum()} large")
  if dots[0].any() or dots[-1].any():
    sys.exit("a dot touches the edge of the band: BAND is too tight")

  # One shape for both kinds: each dot with the room it swells into, white round the small ones and
  # mid grey round the large ones. The shader reads the grey to tell which kind it is beside, since
  # a small dot grows much further than a large one. Half size is plenty.
  shape = np.zeros(band.shape, np.float32)
  for kind, grey in ((~small, LARGE_GREY), (small, 1.0)):
    room = ndi.distance_transform_edt(~np.isin(dots, each[kind])) <= ROOM
    shape[room] = grey
  picture = Image.fromarray((shape * 255).round().astype(np.uint8), "L").resize((width // 2, (bottom - top) // 2), Image.BILINEAR)
  picture.save(HERE / "pieces" / "dots.png", optimize=True)
  print(f"pieces/dots.png: {picture.width}x{picture.height}, {(HERE / 'pieces' / 'dots.png').stat().st_size / 1024:.0f} KB")

  # How the loop swells each dot: the light in and around it, against the first frame's.
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(LOOP), "-vf", f"crop={width}:{bottom - top}:0:{top},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, check=True).stdout
  frames = np.frombuffer(raw, np.uint8).reshape(-1, bottom - top, width)
  length = len(frames)
  around = ndi.grey_dilation(dots, size=(9, 9))
  light = np.array([ndi.sum(frame.astype(np.float32), around, each) for frame in frames])
  grown = light / light[0]

  # When the swell reaches each dot: a straight line across the picture.
  peak = np.array([np.average(np.arange(length), weights=np.maximum(grown[:, d] - 1, 0) ** 2) for d in range(count)]) / 24
  line = np.polyfit(across / width, peak, 1)
  miss = np.abs(peak - np.polyval(line, across / width))
  print(f"{length} frames; the swell is at a dot {line[1]:.3f} + {line[0]:.3f} x seconds in, x from 0 to 1 across the picture "
        f"(off by {miss.mean():.3f} s on average, {miss.max():.3f} at worst)")

  # How far each kind has grown, frame by frame around that moment, as a distance added to its radius.
  tables, reach = {}, {}
  for name, kind in (("SMALL", small), ("LARGE", ~small)):
    radius = np.sqrt(np.median(area[kind]) / np.pi)
    moment = np.polyval(line, across[kind] / width) * 24
    rows = []
    for offset in range(-SPAN, SPAN + 1):
      at = (moment + offset) % length
      low = np.floor(at).astype(int) % length
      part = at - np.floor(at)
      values = grown[:, kind]
      pick = np.arange(kind.sum())
      rows.append(np.median(values[low, pick] * (1 - part) + values[(low + 1) % length, pick] * part))
    added = radius * (np.sqrt(np.maximum(np.array(rows), 1)) - 1)
    added[[0, -1]] = 0
    reach[name] = added.max()
    tables[name] = added / added.max()
    print(f"{name.lower()} dots: radius {radius:.2f} px of the still, {added.max():.2f} more at the swell's height "
          f"({added.max() / height:.5f} of the picture's height); swollen for {(tables[name] > 0.5).sum() / 24:.2f} s")

  glsl = "\n".join(f"const float {name}[{2 * SPAN + 1}] = float[{2 * SPAN + 1}](" + ", ".join(f"{v:.3f}" for v in values) + ");"
                   for name, values in tables.items())
  shader = (HERE / "effects" / "swell.template.glsl").read_text().replace("// TABLES", glsl)
  (HERE / "effects" / "swell.glsl").write_text(shader)
  print(f"wrote effects/swell.glsl, {len(shader)} bytes")
  print("for scene.jsonc:")
  print(f'  "values": {{ "sweep": [{line[1]:.3f}, {line[0]:.3f}], "seconds": {length / 24:.4f} }}')
  print(f'  "reach": [{reach["SMALL"] / height:.5f}, {reach["LARGE"] / height:.5f}]')


if __name__ == "__main__":
  main()
