#!/usr/bin/python
"""Measure the shipped Lumon loop's motion: the numbers the scene's three shaders carry.

Usage: measure.py [loop]

Prints, from the loop and the still:
  the lines   where they are, how fast a light runs along one, when each light's head is at the
              left edge, and how each tail fades and where it ends (effects/comets.glsl)
  the globe   the oval's middle and half-widths, how fast the light goes round and where it
              would be at the cycle's start (effects/orbit.glsl and scene.jsonc)
  the words   where the letters are, and when each is halfway down and halfway back
              (effects/dim.glsl)
The shaders are written by hand from these; nothing else is taken from the loop.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.optimize import least_squares

THEMES = Path("/usr/share/omarchy/themes/lumon/backgrounds")
LOOP = sys.argv[1] if len(sys.argv) > 1 else str(THEMES / "loops" / "01-united-in-severance.mp4")
W, H, FPS = 3840, 2160, 24


def crop(x, y, w, h):
  """That part of every frame of the loop. Even sizes and places: the video's colour is stored at half size."""
  x, y, w, h = x - x % 2, y - y % 2, w + w % 2, h + h % 2
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", LOOP, "-vf", f"crop={w}:{h}:{x}:{y},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
  return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def smooth(x):
  x = np.clip(x, 0, 1)
  return x * x * (3 - 2 * x)


def main():
  still = np.asarray(Image.open(THEMES / "01-united-in-severance.webp").convert("L")).astype(np.float32)
  lines(still)
  globe(still)
  words(still)


def lines(still):
  rows = np.flatnonzero((still > 120).mean(1) > 0.6)
  bands = np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1)
  print("lines: middles at " + ", ".join(f"{(b[0] + b[-1] + 1) / 2 / H:.5f}" for b in bands) + f" of the height, {len(bands[0])} px thick")
  top = bands[0][0] - 30
  frames = crop(0, top, W, bands[-1][-1] + 30 - top)
  count = len(frames)
  seconds = count / FPS
  light = []
  for band in bands:
    mid = slice(band[1] - top, band[-1] - top)
    rest = frames[0, mid].mean(0)
    light.append((frames[:, mid].mean(1) - rest) / (255 - rest))
  light = np.array(light)  # line, frame, x: how far towards white
  speeds, enters = [], []
  for one in light:
    heads = np.array([np.flatnonzero(row > 0.3).max() if (row > 0.3).any() else -1 for row in one])
    inside = np.flatnonzero((heads > 300) & (heads < 3500))
    run = max(np.split(inside, np.flatnonzero(np.diff(inside) > 1) + 1), key=len)
    slope, start = np.polyfit(run / FPS, heads[run], 1)
    speeds.append(slope)
    enters.append(-start / slope)
  speed = float(np.mean(speeds))
  print(f"  a light runs {speed:.1f} px a second, {speed / W:.4f} of the width; heads at the left edge at " + ", ".join(f"{e:.2f}" for e in enters) + " s")
  # Each tail: full for a while behind the head, then fading, then cut off. Fitted to the light behind the head.
  behind = np.arange(-60, 2200, 10)
  for i, one in enumerate(light):
    total, seen = np.zeros(len(behind)), np.zeros(len(behind))
    for k in range(0, count, 2):
      x = ((k / FPS - enters[i]) % seconds) * speed - behind
      ok = (x > 30) & (x < W - 30)
      total[ok] += one[k, np.clip(x.astype(int), 0, W - 1)][ok]
      seen[ok] += 1
    shape = total / np.maximum(seen, 1)
    def model(p):
      lead, rise, hold, fade, end = p
      s = behind + lead
      return FULL * smooth(s / rise) * np.exp(-np.maximum(s - hold, 0) / fade) * (1 - smooth((s - 0.8 * end) / (0.2 * end)))
    FULL = shape.max()
    fit = least_squares(lambda p: model(p) - shape, [25, 70, 200, 300, 1000], bounds=([0, 20, 50, 50, 300], [80, 200, 500, 2000, 3000])).x
    print(f"  line {i + 1}: full {FULL:.2f}; starts {fit[0]:.0f} px ahead of where it is 0.3, rises over {fit[1]:.0f}, holds to {fit[2]:.0f}, "
          f"fades by {fit[3]:.0f} ({fit[3] / W:.3f}), ends at {fit[4]:.0f} ({fit[4] / W:.3f}); off by {np.abs(model(fit) - shape).mean():.3f}")


def globe(still):
  x0, y0, w, h = 1520, 710, 800, 450
  part = still[y0:y0 + h, x0:x0 + w]
  ys, xs = np.nonzero(part > 150)
  cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
  a, b = (xs.max() - xs.min()) / 2 - 2.5, (ys.max() - ys.min()) / 2 - 3.5  # to the middle of the stroke
  frames = crop(x0, y0, w, h)
  angles = np.linspace(0, 2 * np.pi, 720, endpoint=False)
  step = np.hypot(a * np.sin(angles), b * np.cos(angles)) * (2 * np.pi / 720)
  way, round_ = np.cumsum(step) - step / 2, step.sum()
  at = [cy + b * np.sin(angles), cx + a * np.cos(angles)]
  rest = ndi.map_coordinates(frames[0], at, order=1)
  light = np.array([(ndi.map_coordinates(f, at, order=1) - rest) / (255 - rest) for f in frames])
  print(f"globe: oval's middle ({(cx + x0) / W:.4f}, {(cy + y0) / H:.5f}), half-widths to the stroke's middle {a / H:.5f} x {b / H:.5f} of the height, "
        f"{round_ / H:.4f} round")
  heads, previous = {}, None
  for k, row in enumerate(light):
    lit = row > 0.3
    if not lit.any():
      continue
    leading = np.array([way[i] for i in np.flatnonzero(lit) if not lit[(i + 1) % 720]])
    if previous is None:
      head = leading.max()
    else:
      turned = leading + round_ * np.round((previous - leading) / round_)
      turned = np.where(turned < previous - 50, turned + round_, turned)
      head = turned[np.abs(turned - previous).argmin()]
    heads[k], previous = head, head
  frames_lit = np.array(sorted(heads))
  steady = frames_lit[(frames_lit > 40) & (frames_lit < 200)]
  slope, start = np.polyfit(steady / FPS, [heads[k] for k in steady], 1)
  print(f"  lit from frame {frames_lit[0]} to {frames_lit[-1]}; the head goes {slope:.1f} px a second, {slope / round_:.5f} rounds; "
        f"it would be at the right end {-start / slope:.2f} s into the cycle")


def words(still):
  x0, y0, w, h = 1560, 1440, 720, 70
  part = still[y0:y0 + h, x0:x0 + w]
  lit = part > 90
  across = np.flatnonzero(lit.any(0))
  letters = np.split(across, np.flatnonzero(np.diff(across) > 1) + 1)
  ground = np.median(part[~lit])
  frames = crop(x0, y0, w, h)
  left = np.array([[(f[:, l[0]:l[-1] + 1][lit[:, l[0]:l[-1] + 1]] - ground).mean() for l in letters] for f in frames])
  left /= left[0]
  print(f"words: {len(letters)} letters, left edges at " + ", ".join(f"{(l[0] + x0) / W:.4f}" for l in letters) + f"; last ends {(letters[-1][-1] + x0) / W:.4f}")
  def halfway(series, rising):
    low = series.min()
    level = (1 + low) / 2
    for k in range(1, len(series)):
      a, b = series[k - 1], series[k]
      if (a < level <= b) if rising else (a > level >= b):
        return (k - 1 + (level - a) / (b - a)) / FPS
  for i, series in enumerate(left.T):
    print(f"  letter {i + 1}: down to {series.min():.2f}; halfway down at {halfway(series, False):.2f} s, halfway back at {halfway(series, True):.2f} s")


if __name__ == "__main__":
  main()
