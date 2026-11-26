#!/usr/bin/python
"""Make the Hackerman scene's light map and its shader from the still's shipped loop.

Usage: cut.py [width]

In the loop a wave of light crosses the wireframe mountains, from the far ridge towards the viewer.
Each place lights up once: the lines there glow, then fade. So the whole loop is three things, and
this measures them from it:

  where the light falls, and how much   pieces/light.webp, a grey picture: the area's shape
  when it is at its height in each place a polynomial of the place, written into the shader
  how it rises and falls                 the same everywhere: a bell SPREAD frames wide

effects/pass.glsl is written from these. The light is a white with a little less red in it, and
adds less to a colour the nearer that colour already is to full, which is what the loop's
colours do: measured there, a channel a third of the way up takes nearly all of the light, one
two thirds up takes two thirds of it, and one almost full takes a fifth.
"""

import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/hackerman/backgrounds")
LOOP = THEMES / "loops" / "1-synth-scape.mp4"
WIDE = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
TALL = WIDE * 2720 // 3840
TOP, BOTTOM = 0.558824, 0.911765  # the rows the light reaches, with room, as shares of the still's height
SPREAD = float(sys.argv[2]) if len(sys.argv) > 2 else 5.2  # how wide the bell of light is in every place, in frames (its standard deviation)
DEGREE = 4
MIDDLE = 0.7                      # the polynomial counts down from this height, to keep its numbers small
LIT = 8                           # levels a place must gain to count as lit when the timing is measured
QUALITY = 82
TINT = np.array([0.75, 1.0, 1.0], np.float32)  # the light's colour


def room(colour):
  """How much of the light each channel of a colour takes: less the fuller it already is."""
  return TINT * (1 - (colour / 255) ** 3)


def main():
  y0, y1 = round(TOP * TALL), round(BOTTOM * TALL)
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(LOOP), "-vf", f"scale={WIDE}:{TALL}:flags=area,crop={WIDE}:{y1 - y0}:0:{y0}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, y1 - y0, WIDE, 3).astype(np.float32)
  count = len(loop)
  first = loop[0]
  change = loop - first
  del loop
  light = change.mean(-1)
  most = light.max(0)
  lit = most > LIT

  # When the light is at its height in each place, smoothed over its neighbours.
  smooth = ndi.gaussian_filter1d(light, 2.0, axis=0)
  at = np.clip(smooth.argmax(0), 1, count - 2)
  a, b, c = (np.take_along_axis(smooth, (at + step)[None], 0)[0] for step in (-1, 0, 1))
  peak = at + 0.5 * (a - c) / np.minimum(a - 2 * b + c, -1e-6)
  weight = lit * most
  blur = 10 * WIDE / 1920
  peak = ndi.gaussian_filter(peak * weight, blur) / np.maximum(ndi.gaussian_filter(weight, blur), 1e-3)
  del smooth

  # The same, as a polynomial of the place: across from the middle, down from MIDDLE.
  ys, xs = np.mgrid[0:y1 - y0, 0:WIDE]
  u = (xs + 0.5) / WIDE - 0.5
  v = (ys + y0 + 0.5) / TALL - MIDDLE
  powers = [(i, j) for i in range(DEGREE + 1) for j in range(DEGREE + 1 - i)]
  design = np.stack([u[lit] ** i * v[lit] ** j for i, j in powers], -1)
  coefficients, *_ = np.linalg.lstsq(design * weight[lit][:, None] ** 0.5, peak[lit] * weight[lit] ** 0.5, rcond=None)
  when = sum(k * u ** i * v ** j for k, (i, j) in zip(coefficients, powers))
  print(f"the light peaks between frame {peak[lit].min():.1f} and {peak[lit].max():.1f} of {count}; "
        f"the polynomial is {np.sqrt(((when - peak)[lit] ** 2).mean()):.2f} frames from it")

  # How much light each place gets: the amount that fits the loop best, given when and how it comes.
  takes = room(first)
  above, below = np.zeros_like(most), np.zeros_like(most)
  for k in range(count):
    pulse = bell(k - when, count)
    above += pulse * (change[k] * takes).sum(-1)
    below += pulse ** 2 * (takes ** 2).sum(-1)
  amount = np.clip(above / np.maximum(below, 1e-6), 0, None)
  amount[below < 0.5] = 0
  # Nothing outside what the light reaches: the loop's grain is not light.
  reach = ndi.gaussian_filter(ndi.binary_dilation(lit, iterations=max(1, WIDE // 480)).astype(np.float32), 2 * WIDE / 1920)
  amount *= reach
  full = float(np.percentile(amount[lit], 99.95))
  picture = (np.clip(amount / full, 0, 1) * 255).round().astype(np.uint8)
  Image.fromarray(picture, "L").save(HERE / "pieces" / "light.webp", quality=QUALITY, method=6)
  size = (HERE / "pieces" / "light.webp").stat().st_size
  print(f"pieces/light.webp: {WIDE}x{y1 - y0}, {size // 1024 + 1} KB; white is {full:.1f} levels of light, {full / 255:.4f} of white")

  shader = SHADER.format(when=" +\n         ".join(f"{number(k)} * {term(i, j)}" for k, (i, j) in zip(coefficients, powers)),
                         count=count, spread=SPREAD, middle=MIDDLE, tint=", ".join(number(k) for k in TINT))
  (HERE / "effects" / "pass.glsl").write_text(shader)
  # The scene file holds the two numbers that go with the picture: how much light white stands for, and the cycle.
  scene = (HERE / "scene.jsonc").read_text()
  scene, changed = re.subn(r'"amount": [0-9.]+, "seconds": [0-9.]+', f'"amount": {full / 255:.4f}, "seconds": {count / 24:.4f}', scene)
  if changed != 1:
    sys.exit("scene.jsonc has no \"amount\" and \"seconds\" to set")
  (HERE / "scene.jsonc").write_text(scene)
  print(f"effects/pass.glsl: {len(shader)} bytes; scene.jsonc: \"amount\" {full / 255:.4f}, \"seconds\" {count / 24:.4f}")

  # How well the three together give the loop back, with the picture as it was saved.
  saved = np.asarray(Image.open(HERE / "pieces" / "light.webp").convert("L")).astype(np.float32) / 255 * full
  apart, moved, dot, ours, theirs = [], [], 0.0, 0.0, 0.0
  for k in range(count):
    model = np.minimum(first + (saved * bell(k - when, count))[..., None] * takes, 255) - first
    apart.append(np.abs(model - change[k])[lit].mean())
    moved.append(np.abs(change[k])[lit].mean())
    dot += (model * change[k]).sum()
    ours += (model ** 2).sum()
    theirs += (change[k] ** 2).sum()
  print(f"against the loop, where it is lit: {np.mean(apart):.2f} levels apart on average, where the loop changes {np.mean(moved):.2f}; "
        f"the two changes agree {dot / np.sqrt(ours * theirs):.3f}")


def bell(x, count):
  """The light in one place, x frames from its height: a bell, and the cycle comes round."""
  x = x - count * np.floor(x / count + 0.5)
  return np.exp(-0.5 * (x / SPREAD) ** 2)


def number(k):
  """A number a shader takes as one with a fraction: OpenGL ES will not turn a whole number into one."""
  text = f"{k:.5g}"
  return text if "." in text or "e" in text else text + ".0"


def term(i, j):
  return " * ".join(["u"] * i + ["v"] * j) or "1.0"


SHADER = """// A wave of light crosses the wireframe mountains, from the far ridge towards
// the viewer. Each place lights up once in the cycle: its lines glow, then fade.
//
// The area's shape says where the light falls and how much. `when` says at
// which moment of the cycle it is at its height in a place, and the light comes
// up and goes down around that moment as a bell, the same everywhere. cut.py
// measured all three from the still's shipped loop, and wrote this file.

uniform float amount; // how much light the brightest place gets, as a share of white

const float FRAMES = {count}.0; // the cycle, in the frames the times below are counted in
const float SPREAD = {spread}; // how wide the bell of light is, in frames

// The frame at which the light is at its height at a place: a polynomial of how
// far across from the middle it is, and how far down from {middle} of the height.
float when(vec2 uv) {{
  float u = uv.x - 0.5;
  float v = uv.y - {middle};
  return {when};
}}

vec4 effect(vec2 uv) {{
  vec3 colour = still(uv).rgb;
  // Frames since the light was at its height here, in whichever turn of the
  // cycle is nearest, so the end of one turn runs into the start of the next.
  float since = phase * FRAMES - when(uv);
  since -= FRAMES * floor(since / FRAMES + 0.5);
  float light = amount * exp(-0.5 * since * since / (SPREAD * SPREAD));
  // A white with a little less red in it, which adds less to a colour the
  // fuller that colour already is.
  return vec4(colour + light * vec3({tint}) * (1.0 - colour * colour * colour), 1.0);
}}
"""


if __name__ == "__main__":
  main()
