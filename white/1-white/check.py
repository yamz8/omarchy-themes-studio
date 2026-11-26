#!/usr/bin/python
"""Check the White scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, and compares
each with the same frame of the shipped loop, both at 1920x1080: how far the two motions are
apart, against how far the loop itself moves the picture, and whether the folds' edges stay as
sharp while they move. Fails if the scene has drifted from the loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/white/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH, FRAMES = 1920, 1080, 24, 24, 288
# ffmpeg's quick conversion to RGB reads this loop almost two levels dark; the careful one reads it true.
EXACT = "area+accurate_rnd+full_chroma_int"


def main():
  video = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "1-white.mp4"), "-vf", f"scale={W}:{H}:flags={EXACT}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
  still = np.asarray(Image.open(THEMES / "1-white.webp").convert("RGB").resize((W, H), Image.BOX)).astype(int)
  plain = draw(3, "--settling", "1")   # the still as the player itself draws it
  apart, moved, together, crisp_ours, crisp_theirs = [], [], [], [], []
  where = np.zeros((H, W))
  first = theirs_first = None
  for start in range(0, FRAMES, BATCH):
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(BATCH), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True, stderr=subprocess.DEVNULL)
      for k in range(BATCH):
        ours = np.asarray(Image.open(f"{out}/{k:04d}.ppm")).astype(int)
        theirs = np.frombuffer(video.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3).astype(int)
        if first is None:
          first, theirs_first = ours, theirs
          rest = np.abs(ours - plain).max()
          shift = np.abs(theirs - still).mean()
        # What is compared is the motion, so each is measured from its own first frame.
        a, b = (ours - first).astype(float), (theirs - theirs_first).astype(float)
        apart.append(np.abs(a - b).mean())
        moved.append(np.abs(b).mean())
        where = np.maximum(where, ndi.uniform_filter(np.abs(a - b).mean(-1), 31))
        together.append(float((a * b).sum() / max(np.sqrt((a * a).sum() * (b * b).sum()), 1e-9)) if moved[-1] > 0.5 else np.nan)
        if start + k == 6:
          # The player brings an effect up over its first 0.4 seconds by blending it with the still.
          coming_up = steep(ours) / steep(first)
        elif (start + k) % 12 == 6:
          crisp_ours.append(steep(ours) / steep(first))
          crisp_theirs.append(steep(theirs) / steep(theirs_first))
        if start + k == FRAMES // 2:
          grain = np.abs(b - ndi.uniform_filter(b, (5, 5, 1))).mean()
          busiest = np.abs(b).max(-1)
  video.stdout.close()
  video.wait()
  apart, moved, together = map(np.array, (apart, moved, together))
  y, x = np.unravel_index(where.argmax(), where.shape)
  print(f"{FRAMES} frames against the loop, at {W}x{H}:")
  print(f"  at rest the scene is the still as the player draws it, to within {rest} levels; the loop's first frame is {shift:.2f} levels from the still")
  print(f"  the loop moves the picture {moved.mean():.2f} levels on average, {moved.max():.2f} at its furthest; halfway round, {(busiest > 8).mean():.1%} of it has changed by more than 8 levels")
  print(f"  the scene's motion is {apart.mean():.2f} levels from the loop's on average, {apart.max():.2f} on its worst frame; the loop's own grain is {grain:.2f}")
  print(f"  the two motions agree {np.nanmean(together):.3f} on average, {np.nanmin(together):.3f} at worst (1 is the same motion)")
  print(f"  moving, the scene's steepest edges are {np.mean(crisp_ours):.3f} as steep as at rest ({min(crisp_ours):.3f} at worst); the loop's {np.mean(crisp_theirs):.3f} ({min(crisp_theirs):.3f})")
  print(f"  while the player brings the effect up, a quarter of a second in, they are {coming_up:.3f} as steep")
  print(f"  where they differ most: around {x / W:.2f} across, {y / H:.2f} down, {where.max():.1f} levels over a patch 31 pixels wide")
  print(f"  last frame to first, the scene steps {step():.3f} levels, the loop {np.abs(theirs - theirs_first).mean():.3f}")
  if apart.max() > 0.8 or np.nanmin(together) < 0.95 or rest > 0 or min(crisp_ours) < 0.95:
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


def draw(at, *more):
  """One moment of the scene, as the player draws it."""
  with tempfile.TemporaryDirectory() as out:
    subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(at), "--size", f"{W}x{H}", "--out", f"{out}/frame.ppm", *more],
                   check=True, stderr=subprocess.DEVNULL)
    return np.asarray(Image.open(f"{out}/frame.ppm")).astype(int)


def steep(frame):
  """How steep the steepest edges in a frame are, wherever they have moved to."""
  grey = frame.mean(-1)
  slope = np.hypot(ndi.sobel(grey, 0), ndi.sobel(grey, 1))
  return slope[slope > np.percentile(slope, 98.5)].mean()


def step():
  return np.abs(draw((FRAMES - 1) / FPS) - draw(FRAMES / FPS)).mean()


if __name__ == "__main__":
  main()
