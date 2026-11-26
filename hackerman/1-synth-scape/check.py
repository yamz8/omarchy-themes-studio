#!/usr/bin/python
"""Check the Hackerman scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, and compares
each with the same frame of the shipped loop. Each is measured from its own first frame, so what
is compared is the light that passes, not the video's colour conversion. Fails if the scene has
drifted from the loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/hackerman/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 1920, 1360, 24, 23
LIT = 8  # levels a place gains in the loop to count as lit


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "1-synth-scape.mp4"), "-vf", f"scale={W}:{H}:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
  count = len(loop)
  theirs = loop.astype(np.int16) - loop[0].astype(np.int16)
  lit = theirs.mean(-1).max(0) > LIT
  rows = np.where(lit.any(1))[0]
  band = slice(rows[0], rows[-1] + 1)

  ours = np.zeros_like(theirs)
  first = None
  for start in range(0, count, BATCH):
    with tempfile.TemporaryDirectory() as out:
      n = min(BATCH, count - start)
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(n), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True, stderr=subprocess.DEVNULL)
      for k in range(n):
        frame = np.asarray(Image.open(f"{out}/{k:04d}.ppm")).astype(np.int16)
        if first is None:
          first = frame
        ours[start + k] = frame - first
  with tempfile.TemporaryDirectory() as out:
    subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(count / FPS), "--size", f"{W}x{H}", "--out", f"{out}/next.ppm"],
                   check=True, stderr=subprocess.DEVNULL)
    seam = np.abs(np.asarray(Image.open(f"{out}/next.ppm")).astype(np.int16) - (first + ours[-1])).mean()

  apart = np.array([np.abs(ours[k] - theirs[k])[lit].mean() for k in range(count)])
  moved = np.array([np.abs(theirs[k])[lit].mean() for k in range(count)])
  a, b = ours.astype(np.float32), theirs.astype(np.float32)
  agree = float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))
  print(f"{count} frames against the loop, each from its own first frame:")
  print(f"  where the loop is lit ({lit.mean():.1%} of the picture) it changes {moved.mean():.2f} levels on average, {moved.max():.2f} on its busiest frame")
  print(f"  the scene is {apart.mean():.2f} levels from it on average, {apart.max():.2f} on its worst frame; the two changes agree {agree:.3f} (1 is the same change)")
  quiet = ~lit
  print(f"  where the loop is not lit, the loop changes {np.mean([np.abs(theirs[k])[quiet].mean() for k in range(0, count, 4)]):.2f} levels and the scene "
        f"{np.mean([np.abs(ours[k])[quiet].mean() for k in range(0, count, 4)]):.2f}")

  # When the light is at its height, from the far ridge to the near slopes, and how bright it is there.
  print("  rows of the picture, far to near: the frame the light peaks at, loop and scene; the light at its height, loop and scene")
  late, gain = [], []
  for top in range(band.start, band.stop, (band.stop - band.start) // 6):
    part = lit[top:top + (band.stop - band.start) // 6]
    if part.sum() < 2000:
      continue
    theirs_light = np.array([theirs[k, top:top + part.shape[0]].mean(-1)[part].mean() for k in range(count)])
    ours_light = np.array([ours[k, top:top + part.shape[0]].mean(-1)[part].mean() for k in range(count)])
    late.append(int(ours_light.argmax()) - int(theirs_light.argmax()))
    gain.append(ours_light.max() / theirs_light.max())
    print(f"    {top / H:.2f}: frame {theirs_light.argmax():2d} and {ours_light.argmax():2d}; {theirs_light.max():5.1f} and {ours_light.max():5.1f} levels")
  print(f"  last frame to first, the scene steps {seam:.2f} levels; the loop steps {np.abs(theirs[-1]).mean():.2f}")

  problems = []
  if agree < 0.9:
    problems.append(f"the two changes agree only {agree:.3f}")
  if max(abs(v) for v in late) > 2:
    problems.append(f"the light peaks {max(abs(v) for v in late)} frames off the loop's somewhere")
  if min(gain) < 0.85 or max(gain) > 1.15:
    problems.append(f"the light is {min(gain):.2f} to {max(gain):.2f} of the loop's")
  if problems:
    sys.exit("the scene has drifted from the loop: " + "; ".join(problems))
  print("the scene follows the shipped loop")


if __name__ == "__main__":
  main()
