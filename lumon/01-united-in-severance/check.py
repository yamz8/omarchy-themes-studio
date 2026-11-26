#!/usr/bin/python
"""Check the Lumon scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, at half the
still's size, and compares each with the same frame of the shipped loop: the light along each of
the five lines, the light round the globe's outline, and how much light each letter has left.
Fails if the scene has drifted from the loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/lumon/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 1920, 1080, 24, 24
LINES = [0.56019, 0.57963, 0.59954, 0.61944, 0.63889]
MIDDLE, RADII = (0.4999, 0.43125), (0.15833, 0.07963)  # the oval, as the scene has it
LETTERS = [1600, 1639, 1679, 1697, 1732, 1767, 1826, 1846, 1910, 1948, 1982, 2022, 2057, 2094, 2136, 2177, 2215, 2245]  # left edges at 3840 wide
TEXT = (1464, 1487)


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "01-united-in-severance.mp4"), "-vf", f"scale={W}:{H}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
  count = len(loop)
  angles = np.linspace(0, 2 * np.pi, 720, endpoint=False)
  oval = [MIDDLE[1] * H + RADII[1] * H * np.sin(angles), MIDDLE[0] * W + RADII[0] * H * np.cos(angles)]
  rows = [round(y * H - 0.5) for y in LINES]
  text = np.zeros((H, W), bool)
  text[TEXT[0] // 2:TEXT[1] // 2 + 1] = loop[0][TEXT[0] // 2:TEXT[1] // 2 + 1] > 90
  ground = float(np.median(loop[0][TEXT[0] // 2 - 12:TEXT[0] // 2 - 4, 800:1120]))

  def measure(frame, rest):
    """The light along the lines and round the oval, as shares of the way to white, and what each letter has left."""
    frame = frame.astype(np.float32)
    lines = np.array([(frame[y] - rest[y]) / np.maximum(255 - rest[y], 1) for y in rows])
    around = (ndi.map_coordinates(frame, oval, order=1) - ndi.map_coordinates(rest, oval, order=1)) / np.maximum(255 - ndi.map_coordinates(rest, oval, order=1), 1)
    letters = []
    for a, b in zip(LETTERS[:-1], LETTERS[1:]):
      part = text[:, a // 2:b // 2]
      letters.append((frame[:, a // 2:b // 2][part] - ground).mean() / max((rest[:, a // 2:b // 2][part] - ground).mean(), 1))
    return lines, around, np.array(letters)

  ours_rest = theirs_rest = None
  lines, around, letters, strong, moved = [], [], [], [], []
  for start in range(0, count, BATCH):
    some = min(BATCH, count - start)
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(some), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True, stderr=subprocess.DEVNULL)
      for k in range(some):
        frame = np.asarray(Image.open(f"{out}/{k:04d}.ppm").convert("L"))
        if ours_rest is None:
          ours_rest, theirs_rest = frame.astype(np.float32), loop[0].astype(np.float32)
          rest = (np.abs(frame.astype(int) - loop[0]) > 48).mean()
        a, b = measure(frame, ours_rest), measure(loop[start + k], theirs_rest)
        lines.append((a[0], b[0])); around.append((a[1], b[1])); letters.append((a[2], b[2]))
        strong.append((np.abs(frame.astype(int) - loop[start + k]) > 48).mean())
        moved.append((np.abs(loop[start + k].astype(int) - loop[0]) > 48).mean())
  lines, around, letters = np.array(lines), np.array(around), np.array(letters)
  strong, moved = np.array(strong), np.array(moved)
  print(f"{count} frames against the loop, at {W}x{H}:")
  print(f"  {strong.mean():.3%} of pixels differ strongly on average, {strong.max():.3%} on the worst frame, {rest:.3%} at rest; "
        f"the loop's own motion changes {moved.mean():.3%}, {moved.max():.3%} at its furthest")

  apart = np.abs(lines[:, 0] - lines[:, 1])
  lit = lines[:, 1] > 0.15
  print(f"  lights on the lines: {apart.mean():.3f} of the way to white from the loop's on average, {apart[lit].mean():.3f} where the loop is lit")
  heads = []
  for line in range(5):
    for k in range(count):
      ours, theirs = (np.flatnonzero(lines[k, which, line] > 0.4) for which in (0, 1))
      if len(ours) and len(theirs) and 40 < theirs.max() < W - 40:
        heads.append(ours.max() - theirs.max())
  heads = np.array(heads) * 2
  print(f"    a light's head is {np.abs(heads).mean():.1f} px of 3840 from the loop's on average, {np.percentile(np.abs(heads), 99):.0f} for 99 in 100")

  apart = np.abs(around[:, 0] - around[:, 1])
  lit = around[:, 1] > 0.15
  print(f"  light round the globe: {apart.mean():.3f} of the way to white from the loop's on average, {apart[lit].mean():.3f} where the loop is lit")
  first, last = np.flatnonzero((around[:, 1] > 0.3).any(1))[[0, -1]]
  ours_on = np.flatnonzero((around[:, 0] > 0.3).any(1))
  print(f"    lit from frame {first} to {last} in the loop and {ours_on[0]} to {ours_on[-1]} in the scene")

  apart = np.abs(letters[:, 0] - letters[:, 1])
  print(f"  words: the light a letter has left is {apart.mean():.3f} from the loop's on average, {apart.max():.2f} at worst; "
        f"lowest {letters[:, 1].min():.2f} in the loop and {letters[:, 0].min():.2f} in the scene")
  if strong.mean() > moved.mean() / 2 or np.abs(heads).mean() > 12 or apart.mean() > 0.03:
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


if __name__ == "__main__":
  main()
