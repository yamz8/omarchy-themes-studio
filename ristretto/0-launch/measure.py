#!/usr/bin/python
"""Measure how the shipped Ristretto loop moves its stripes, and write the scene's shader from it.

Usage: measure.py [loop]

The still is five flat stripes on a dark ground: straight down the top of the picture, then
fanning out. In the loop each stripe slides sideways, row by row, on a wave that travels down
it, and the two outer stripes also widen and narrow where they fan out. This follows each stripe
through the loop by its colour, fits the shift of its middle and the change of its width at each
height to one wave of the loop's length, and writes those fits as short tables into
effects/sway.glsl. Nothing is taken from the loop but those numbers.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/omarchy/themes/ristretto/backgrounds/loops/0-launch.mp4"
W, H = 1920, 160  # wide for the sideways motion, few rows: it changes slowly down the picture
GROUND = np.array([28, 14, 0], np.float32)
STRIPES = np.array([[84, 41, 34], [135, 54, 35], [189, 73, 36], [223, 120, 45], [231, 170, 90]], np.float32)
KNOTS = 17
STEP = 6  # every sixth frame is plenty for one slow wave


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", LOOP, "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True).stdout
  frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
  count = len(frames)
  centre0, width0 = place(frames[0])
  times = np.arange(0, count, STEP)
  moved = np.zeros((len(times), 5, H), np.float32)
  wider = np.zeros_like(moved)
  for i, k in enumerate(times):
    centre, width = place(frames[k])
    moved[i], wider[i] = centre - centre0, width - width0

  # Each as p sin + q (cos - 1) over the loop: nothing at its start, and round again.
  turn = 2 * np.pi * times / count
  basis = np.stack([np.sin(turn), np.cos(turn) - 1], 1)
  fit = lambda series: np.linalg.lstsq(basis, series.reshape(len(times), -1), rcond=None)[0].reshape(2, 5, H)
  shift, grow = fit(moved), fit(wider)
  left = np.abs(moved.reshape(len(times), -1) - basis @ shift.reshape(2, -1)).mean()
  print(f"{count} frames; one wave of the loop's length leaves {left * W:.2f} px of {W} unexplained on average")

  # The picture is the same either side of its middle, moving opposite ways.
  inner = (shift[:, 3] - shift[:, 1]) / 2
  outer = (shift[:, 4] - shift[:, 0]) / 2
  breathe = (grow[:, 4] + grow[:, 0]) / 2
  print(f"the middle stripe moves {np.abs(shift[:, 2]).max() * 1000:.2f} thousandths of the width at most; "
        f"the inner pair up to {np.hypot(*inner).max() * 1000:.1f}, the outer pair up to {np.hypot(*outer).max() * 1000:.1f}")

  spacing = (centre0[4] - centre0[0]) / 4
  rows = (np.arange(H) + 0.5) / H
  start = rows[np.flatnonzero(spacing > np.median(spacing[:H // 3]) + 0.0005)[0]]
  fan = np.polyfit(rows[rows > start] - start, spacing[rows > start] - np.median(spacing[:H // 3]), 2)
  print(f"stripes {np.median(spacing[:H // 3]):.4f} of the width apart down to {start:.3f}, then fanning out by {fan[0]:.4f} u^2 + {fan[1]:.4f} u")

  def table(values):
    """A profile down the picture as KNOTS values, each the average of the rows near it."""
    at = np.linspace(0, 1, KNOTS)
    return [float(np.average(values, weights=np.exp(-0.5 * ((rows - a) * KNOTS * 1.6) ** 2))) for a in at]

  tables = {"INNER_SIN": table(inner[0]), "INNER_COS": table(inner[1]), "OUTER_SIN": table(outer[0]), "OUTER_COS": table(outer[1]),
            "WIDER_SIN": table(breathe[0]), "WIDER_COS": table(breathe[1])}
  glsl = "\n".join(f"const float {name}[{KNOTS}] = float[{KNOTS}](" + ", ".join(f"{v:.5f}" for v in values) + ");" for name, values in tables.items())
  shader = (HERE / "effects" / "sway.template.glsl").read_text()
  shader = shader.replace("// TABLES", glsl).replace("APART", f"{np.median(spacing[:H // 3]):.4f}").replace("FAN_FROM", f"{start:.4f}")
  shader = shader.replace("FAN_SQUARE", f"{fan[0]:.4f}").replace("FAN_LINE", f"{fan[1]:.4f}")
  (HERE / "effects" / "sway.glsl").write_text(shader)
  print(f"wrote effects/sway.glsl, {len(shader)} bytes")


def place(frame):
  """The middle and the width of each stripe in each row, as shares of the picture's width.

  A pixel on a stripe's edge is part stripe and part ground; how much of it is stripe is where
  its colour lies between the two, so the middle and width come out finer than a pixel.
  """
  colour = frame.astype(np.float32) - GROUND
  across = np.arange(W, dtype=np.float32)
  centres, widths = [], []
  for stripe in STRIPES:
    way = stripe - GROUND
    share = (colour @ way) / (way @ way)
    off = np.abs(colour - share[..., None] * way).sum(-1)
    cover = np.where(off < 7, np.clip(share, 0, 1), 0)
    # A faint pixel on any stripe's edge is close to the ground, and so close to every stripe's
    # colour: only what is beside pixels that are firmly this stripe's counts as its edge.
    firm = (cover > 0.6).astype(np.float32)
    reach = np.maximum.reduce([np.roll(firm, shift, axis=-1) for shift in range(-3, 4)])
    cover = cover * reach
    width = cover.sum(-1)
    centres.append((cover * across).sum(-1) / np.maximum(width, 1e-6) / W)
    widths.append(width / W)
  return np.array(centres), np.array(widths)


if __name__ == "__main__":
  main()
