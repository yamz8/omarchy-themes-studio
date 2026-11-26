#!/usr/bin/python
"""Check the Rose Pine scene against the loop it would stand in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, at a quarter
of the loop's size, and compares each with the same frame of the shipped loop: how much of the
picture is far from the loop's, against how much the loop itself moves it; where the dark dashes
are; how large the steps between frames are; and the step from the last frame to the first.
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
THEMES = Path("/usr/share/omarchy/themes/rose-pine/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 960, 576, 24, 48
FAR = 12  # levels: further than the video's own colour shift and grain


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "1-funky-shapes.mp4"), "-vf", f"scale={W}:{H}:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
  # The still as the player draws it: a scene settled all the way into it.
  with tempfile.TemporaryDirectory() as out:
    for name, more in (("rest", ["--at", "0"]), ("still", ["--at", "3", "--settling", "1"])):
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), *more, "--size", f"{W}x{H}", "--out", f"{out}/{name}.ppm"], check=True)
    rest = np.abs(np.asarray(Image.open(f"{out}/rest.ppm")).astype(int) - np.asarray(Image.open(f"{out}/still.ppm")).astype(int)).max()
  count = len(loop)
  far, moved, apart, steps_ours, steps_theirs, dashes = [], [], [], [], [], []
  last = first = None
  for start in range(0, count, BATCH):
    n = min(BATCH, count - start)
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(n), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True)
      for k in range(n):
        ours = np.asarray(Image.open(f"{out}/{k:04d}.ppm")).astype(int)
        theirs = loop[start + k].astype(int)
        if first is None:
          first = ours
        far.append((np.abs(ours - theirs).max(-1) > FAR).mean())
        moved.append((np.abs(theirs - loop[0].astype(int)).max(-1) > FAR).mean())
        apart.append(np.abs(ours - theirs).mean())
        if last is not None:
          steps_ours.append(np.abs(ours - last[0]).mean())
          steps_theirs.append(np.abs(theirs - last[1]).mean())
        last = (ours, theirs)
        a, b = dark_dashes(ours), dark_dashes(theirs)
        if len(a) == len(b):
          dashes.append(np.mean([np.hypot(*(b - p).T).min() for p in a]))
  far, moved, apart, dashes = map(np.array, (far, moved, apart, dashes))
  seam = np.abs(last[0] - first).mean()
  print(f"{count} frames against the loop, at {W}x{H}:")
  print(f"  at rest the scene is the still as the player draws it, to within {rest} levels")
  print(f"  the loop moves {moved.mean():.1%} of the picture by more than {FAR} levels on average, {moved.max():.1%} at its most")
  print(f"  the scene is that far from the loop over {far.mean():.2%} of the picture on average, {far.max():.2%} on its worst frame")
  print(f"  mean difference {apart.mean():.2f} levels ({apart[0]:.2f} on the first frame, where nothing has moved: the video's own colour)")
  print(f"  the dark dashes are {dashes.mean():.2f} px from the loop's on average, {dashes.max():.2f} at worst, on {len(dashes)} frames where both show the same number")
  print(f"  steps between frames: the scene's largest {max(steps_ours):.2f} levels, the loop's {max(steps_theirs):.2f}; "
        f"the scene's last frame to its first {seam:.2f}")
  if rest > 0 or far.max() > 0.04 or dashes.mean() > 0.6 or max(steps_ours) > 2.5 * max(steps_theirs) or seam > 2 * max(steps_ours):
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


def dark_dashes(frame):
  """Where the middle of each dark dash is."""
  parts, n = ndi.label(frame[: H // 2, : W // 3].sum(-1) < 330)
  sizes = ndi.sum(np.ones_like(parts), parts, range(1, n + 1))
  return np.array([ndi.center_of_mass(parts == k + 1) for k in range(n) if sizes[k] > 12])


if __name__ == "__main__":
  main()
