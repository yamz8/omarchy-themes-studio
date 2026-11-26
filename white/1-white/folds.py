#!/usr/bin/python
"""Work out how the folds of the white still run, and write the scene's shader with that in it.

Usage: folds.py [still]

The scene moves each fold of the paper across its own edge, on a wave that travels outward from
the grey opening. For that the shader has to know, at every place, how far out among the folds
the place is and which way is across them. This works that out from the still once:

  1. Which way the edges face around each place, from the picture's own shading, turned to point
     away from the opening. Where the picture is flat the folds are taken to ring the opening.
  2. The fold coordinate: the number whose slope is closest to those directions everywhere, so its
     level lines run along the folds. A fold then moves by the same amount along its whole length
     and its edge stays smooth.
  3. That coordinate is smooth enough to be written as a formula, 45 numbers, which go into
     effects/folds.glsl. The scene ships no picture of it.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import fft, ndimage as ndi

HERE = Path(__file__).resolve().parent
STILL = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/omarchy/themes/white/backgrounds/1-white.webp")
WIDE = 960      # the folds are tens of pixels wide; which way they run needs no more than this
SMOOTH = 6.0    # how far, in those pixels, the direction of the folds is averaged over
DEGREE = 8      # of the formula
# The grey opening: its middle and its radii, as shares of the still's width and height.
OPENING = (0.0637, 0.5597, 0.2766, 0.3843)


def main():
  phi = fold_coordinate()
  coef, off = fit(phi)
  write_shader(coef)
  print(f"the fold coordinate runs from 0 to {phi.max():.2f} of the still's height")
  print(f"as a formula of degree {DEGREE}, {len(coef)} numbers: off by {off.mean():.4f} of the height on average, {off.max():.4f} at worst")
  print(f"wrote {HERE / 'effects' / 'folds.glsl'}")


def smoothstep(a, b, s):
  s = np.clip((s - a) / (b - a), 0, 1)
  return s * s * (3 - 2 * s)


def fold_coordinate():
  """For every place, how far out among the folds it is, as a share of the still's height."""
  picture = Image.open(STILL).convert("L")
  w, h = WIDE, round(WIDE * picture.height / picture.width)
  soft = lambda a, s: ndi.gaussian_filter(a, s, mode="nearest")
  grey = soft(np.asarray(picture.resize((w, h), Image.BOX)).astype(np.float32), 1.0)
  gx, gy = ndi.sobel(grey, axis=1, mode="nearest"), ndi.sobel(grey, axis=0, mode="nearest")
  # Which way the edges face around each place, and how sure that is.
  xx, xy, yy = (soft(v, SMOOTH) for v in (gx * gx, gx * gy, gy * gy))
  angle = 0.5 * np.arctan2(2 * xy, xx - yy)
  strong = xx + yy
  sure = np.sqrt((xx - yy) ** 2 + 4 * xy ** 2) / (strong + 1e-6)

  # A canvas three times the picture: the folds run off the screen, and a fit that stopped at the
  # screen's edge would bend its lines to meet the edge square on.
  big_h, big_w = 3 * h, 3 * w
  ys, xs = np.mgrid[0:big_h, 0:big_w].astype(np.float32)
  xs -= w
  ys -= h
  cx, cy, rx, ry = OPENING[0] * w, OPENING[1] * h, OPENING[2] * w, OPENING[3] * h
  out_x, out_y = (xs - cx) / rx ** 2, (ys - cy) / ry ** 2   # straight out from the opening
  length = np.maximum(np.hypot(out_x, out_y), 1e-9)
  out_x, out_y = out_x / length, out_y / length

  def placed(a):
    canvas = np.zeros((big_h, big_w), np.float32)
    canvas[h:2 * h, w:2 * w] = a
    return canvas

  nx, ny = placed(np.cos(angle)), placed(np.sin(angle))
  facing = np.sign(nx * out_x + ny * out_y)
  facing[facing == 0] = 1
  nx, ny = nx * facing, ny * facing
  # The folds are trusted where they are clear and strong, and the opening's rings elsewhere.
  trust = soft(placed(np.clip(sure, 0, 1) * smoothstep(0.02, 0.2, strong / (np.percentile(strong, 90) + 1e-6))), SMOOTH)
  nx, ny = trust * nx + (1 - trust) * out_x, trust * ny + (1 - trust) * out_y
  length = np.maximum(np.hypot(nx, ny), 1e-6)
  nx, ny = soft(nx / length, SMOOTH / 2), soft(ny / length, SMOOTH / 2)
  length = np.maximum(np.hypot(nx, ny), 1e-6)
  nx, ny = nx / length, ny / length

  # The coordinate whose slope is closest to those directions everywhere.
  spread = np.gradient(nx, axis=1) + np.gradient(ny, axis=0)
  spectrum = fft.dctn(spread, type=2, norm="ortho")
  ky = 2 * (np.cos(np.pi * np.arange(big_h) / big_h) - 1)
  kx = 2 * (np.cos(np.pi * np.arange(big_w) / big_w) - 1)
  scale = ky[:, None] + kx[None, :]
  scale[0, 0] = 1
  phi = fft.idctn(spectrum / scale, type=2, norm="ortho")[h:2 * h, w:2 * w]
  return ((phi - phi.min()) / h).astype(np.float64)


def terms():
  return [(i, j) for i in range(DEGREE + 1) for j in range(DEGREE + 1 - i)]


def fit(phi):
  """The coordinate as a sum of 45 smooth shapes, fitted where the folds move: from the opening's rim outward."""
  h, w = phi.shape
  ys, xs = np.mgrid[0:h, 0:w]
  u, v = (xs + 0.5) / w, (ys + 0.5) / h
  moving = np.hypot((u - OPENING[0]) / OPENING[2], (v - OPENING[1]) / OPENING[3]) > 0.7
  across = np.polynomial.chebyshev.chebvander(u.ravel() * 2 - 1, DEGREE)
  down = np.polynomial.chebyshev.chebvander(v.ravel() * 2 - 1, DEGREE)
  shapes = np.stack([across[:, i] * down[:, j] for i, j in terms()], 1)
  coef, *_ = np.linalg.lstsq(shapes[moving.ravel()], phi.ravel()[moving.ravel()], rcond=None)
  return coef, np.abs(shapes @ coef - phi.ravel())[moving.ravel()]


def write_shader(coef):
  rows = [", ".join(f"{c:.7f}" for c in coef[k:k + 5]) for k in range(0, len(coef), 5)]
  numbers = ",\n  ".join(rows)
  count = len(coef)
  (HERE / "effects" / "folds.glsl").write_text(f"""// A slow wave travels outward through the folds of the paper, from the grey
// opening, and moves each fold across its own edge. A fold moves by the same
// amount along its whole length, so its edge stays smooth.
//
// FOLD is where the folds are: a number for every place that grows steadily
// across the folds, outward, as a share of the still's height. It is written
// as a formula, a sum of {count} smooth shapes, which folds.py worked out from
// the still; do not edit the numbers by hand.
//
// A fold's shift is measured against where the wave stands at the start of
// the cycle, so at the start, and each time it comes round, the picture is
// the still exactly. The wave keeps the same speed all the way round.

uniform float amount; // how far a fold moves at most, as a share of the still's height
uniform float wave;   // the length of one wave across the folds, as a share of the still's height

const float TURN = 6.2831853;
// The grey opening: its middle and its radii, as shares of the still. Inside it nothing moves.
const vec2 OPENING_AT = vec2({OPENING[0]}, {OPENING[1]});
const vec2 OPENING_SIZE = vec2({OPENING[2]}, {OPENING[3]});
const int DEGREE = {DEGREE};
const float FOLD[{count}] = float[{count}](
  {numbers});

// The still at a place between its pixels, read through a sharper curve than the plain blend of the
// four nearest: with that blend a fold's hard edge goes soft whenever it sits between pixels, and
// the paper would lose its crispness as soon as it moved. Nine blended reads make sixteen pixels.
vec4 crisp(vec2 uv) {{
  vec2 place = uv / pixel;
  vec2 whole = floor(place - 0.5) + 0.5;
  vec2 f = place - whole;
  vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f));
  vec2 w1 = 1.0 + f * f * (-2.5 + 1.5 * f);
  vec2 w2 = f * (0.5 + f * (2.0 - 1.5 * f));
  vec2 w3 = f * f * (-0.5 + 0.5 * f);
  vec2 mid = w1 + w2;
  vec2 a = (whole - 1.0) * pixel;
  vec2 b = (whole + w2 / mid) * pixel;
  vec2 c = (whole + 2.0) * pixel;
  return (still(vec2(a.x, a.y)) * w0.x + still(vec2(b.x, a.y)) * mid.x + still(vec2(c.x, a.y)) * w3.x) * w0.y +
         (still(vec2(a.x, b.y)) * w0.x + still(vec2(b.x, b.y)) * mid.x + still(vec2(c.x, b.y)) * w3.x) * mid.y +
         (still(vec2(a.x, c.y)) * w0.x + still(vec2(b.x, c.y)) * mid.x + still(vec2(c.x, c.y)) * w3.x) * w3.y;
}}

vec4 effect(vec2 uv) {{
  // The smooth shapes across and down, and their slopes.
  float across[{DEGREE + 1}];
  float across_slope[{DEGREE + 1}];
  float down[{DEGREE + 1}];
  float down_slope[{DEGREE + 1}];
  vec2 at = uv * 2.0 - 1.0;
  across[0] = 1.0; across[1] = at.x; across_slope[0] = 0.0; across_slope[1] = 1.0;
  down[0] = 1.0; down[1] = at.y; down_slope[0] = 0.0; down_slope[1] = 1.0;
  for (int i = 2; i <= DEGREE; i++) {{
    across[i] = 2.0 * at.x * across[i - 1] - across[i - 2];
    across_slope[i] = 2.0 * across[i - 1] + 2.0 * at.x * across_slope[i - 1] - across_slope[i - 2];
    down[i] = 2.0 * at.y * down[i - 1] - down[i - 2];
    down_slope[i] = 2.0 * down[i - 1] + 2.0 * at.y * down_slope[i - 1] - down_slope[i - 2];
  }}
  // How far out among the folds this place is, and which way is across them.
  float fold = 0.0;
  vec2 slope = vec2(0.0);
  int k = 0;
  for (int i = 0; i <= DEGREE; i++) {{
    for (int j = 0; j <= DEGREE - i; j++) {{
      fold += FOLD[k] * across[i] * down[j];
      slope += FOLD[k] * vec2(across_slope[i] * down[j] / aspect, across[i] * down_slope[j]);
      k++;
    }}
  }}
  vec2 way = slope / max(length(slope), 0.000001);

  // Near each edge of the picture only the motion across that edge fades, so a fold slides along
  // the edge and nothing is read from outside the picture.
  float margin = 10.0 * amount;
  vec2 from_edge = min(uv, 1.0 - uv) * vec2(aspect, 1.0);
  way *= smoothstep(0.0, margin, from_edge);

  // The flat inside of the opening stays put; the folds from its rim outward move.
  float reach = smoothstep(0.8, 1.0, length((uv - OPENING_AT) / OPENING_SIZE));
  float turn = TURN * fold / wave;
  float shift = amount * reach * (sin(turn - TURN * phase) - sin(turn));
  vec2 from = uv - shift * way * vec2(1.0 / aspect, 1.0);
  // Where a fold has not moved at all, the still as it is: at the start of the cycle that is
  // everywhere. A twentieth of a pixel away it is read the crisp way already.
  return mix(still(from), crisp(from), clamp(20.0 * abs(shift) / pixel.y, 0.0, 1.0));
}}
""")


if __name__ == "__main__":
  main()
