#!/usr/bin/python
"""Check the Latte scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, and compares
each with the same frame of the shipped loop: how far the two are apart, against how far the
loop itself moves the picture from its still. Fails if the scene has drifted from the loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/catppuccin-latte/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 1536, 1024, 24, 48


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "1-color-fade.mp4"), "-vf", "scale=flags=accurate_rnd+full_chroma_int,format=rgb24", "-f", "rawvideo", "-"],
                       capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
  still = np.asarray(Image.open(THEMES / "1-color-fade.webp").convert("RGB")).astype(int)
  # What is compared is the motion, so each is measured from its own first frame. The video is
  # decoded with ffmpeg's accurate conversion: its quick one comes out about a level dark.
  shift = (loop[0].astype(int) - still).mean()
  apart, moved, together, first = [], [], [], None
  for start in range(0, len(loop), BATCH):
    count = min(BATCH, len(loop) - start)
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(count), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True)
      for k in range(count):
        ours = np.asarray(Image.open(f"{out}/{k:04d}.ppm")).astype(int)
        if first is None:
          first = ours
          rest = np.abs(ours - still).max()
        a = (ours - first).astype(float)
        b = (loop[start + k].astype(int) - loop[0]).astype(float)
        apart.append(np.abs(a - b).mean())
        moved.append(np.abs(b).mean())
        # Do the two move the picture the same way? Their changes, set against each other.
        together.append(float((a * b).sum() / max(np.sqrt((a * a).sum() * (b * b).sum()), 1e-9)) if moved[-1] > 0.5 else np.nan)
  apart, moved, together = map(np.array, (apart, moved, together))
  print(f"{len(loop)} frames against the loop:")
  print(f"  at rest the scene is the still to within {rest} level; the loop's first frame is {abs(shift):.2f} levels from the still on average")
  print(f"  the loop moves the picture {moved.mean():.2f} levels on average, {moved.max():.2f} at its furthest")
  print(f"  the scene's motion is {apart.mean():.2f} levels from the loop's on average, {apart.max():.2f} on its worst frame")
  print(f"  the two motions agree {np.nanmean(together):.3f} on average, {np.nanmin(together):.3f} at worst (1 is the same motion)")
  print(f"  last frame to first, the scene steps {step(HERE, len(loop)):.2f} levels")
  if apart.max() > 0.7 or np.nanmin(together) < 0.85:
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


def step(here, count):
  with tempfile.TemporaryDirectory() as out:
    for name, at in (("last", (count - 1) / FPS), ("first", count / FPS)):
      subprocess.run([RENDER, "--scene-frame", str(here / "scene.jsonc"), "--at", str(at), "--size", f"{W}x{H}", "--out", f"{out}/{name}.ppm"], check=True)
    return np.abs(np.asarray(Image.open(f"{out}/last.ppm")).astype(int) - np.asarray(Image.open(f"{out}/first.ppm")).astype(int)).mean()


if __name__ == "__main__":
  main()
