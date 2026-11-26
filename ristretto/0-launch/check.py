#!/usr/bin/python
"""Check the Ristretto scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, and compares
each with the same frame of the shipped loop: how many pixels differ, and where the middle of
each stripe is in each row. Fails if the scene has drifted from the loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
LOOP = "/usr/share/omarchy/themes/ristretto/backgrounds/loops/0-launch.mp4"
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 960, 640, 24, 48
GROUND = np.array([28, 14, 0], np.float32)
STRIPES = np.array([[84, 41, 34], [135, 54, 35], [189, 73, 36], [223, 120, 45], [231, 170, 90]], np.float32)


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", LOOP, "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
  strong, moved, off, widths, first, last = [], [], [], [], None, None
  print(f"{len(loop)} frames against the loop, at {W}x{H}:")
  for start in range(0, len(loop), BATCH):
    count = min(BATCH, len(loop) - start)
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(count), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True, stderr=subprocess.DEVNULL)
      for k in range(count):
        ours = np.asarray(Image.open(f"{out}/{k:04d}.ppm"))
        theirs = loop[start + k]
        first = ours if first is None else first
        last = ours
        strong.append((np.abs(ours.astype(int) - theirs).max(-1) > 40).mean())
        moved.append((np.abs(theirs.astype(int) - loop[0]).max(-1) > 40).mean())
        # Each is measured from its own first frame: the two are scaled down from different sizes in
        # different ways, which alone puts their edges a little apart, moving or not.
        if start + k == 0:
          ours_are, theirs_are = colours_of(ours), colours_of(theirs)
        (oc, ow), (tc, tw) = place(ours, ours_are), place(theirs, theirs_are)
        if start + k == 0:
          oc0, ow0, tc0, tw0 = oc, ow, tc, tw
          print(f"  at rest the two measure {np.abs(oc - tc)[ow > 0.004].mean() * 1920:.2f} px apart in stripe middles and "
                f"{np.abs(ow - tw)[ow > 0.004].mean() * 1920:.2f} px in widths, from how each is scaled down")
        seen = (ow > 0.004) & (tw > 0.004) & (ow0 > 0.004) & (tw0 > 0.004)
        off.append(np.where(seen, np.abs((oc - oc0) - (tc - tc0)), np.nan))
        widths.append(np.where(seen, np.abs((ow - ow0) - (tw - tw0)), np.nan))
  strong, moved, off, widths = np.array(strong), np.array(moved), np.array(off), np.array(widths)
  rest = (np.abs(first.astype(int) - loop[0]).max(-1) > 40).mean()
  print(f"  {strong.mean():.3%} of pixels differ strongly on average, {strong.max():.3%} on the worst frame, {rest:.3%} at rest; "
        f"the loop's own motion changes {moved.mean():.2%}, {moved.max():.2%} at its furthest")
  print(f"  how far stripe middles have moved: {np.nanmean(off) * 1920:.2f} px of 1920 from the loop's on average, {np.nanpercentile(off, 99) * 1920:.2f} for 99 in 100, "
        f"{np.nanmax(off) * 1920:.1f} at worst")
  by_stripe = np.nanmean(off, axis=(0, 2)) * 1920
  print("    by stripe, left to right: " + ", ".join(f"{v:.2f}" for v in by_stripe))
  lower = np.nanmean(off[:, :, int(H * 0.6):]) * 1920
  print(f"    where they fan out (the lowest two fifths): {lower:.2f} px on average")
  print(f"  how much stripe widths have changed: {np.nanmean(widths) * 1920:.2f} px from the loop's on average, {np.nanpercentile(widths, 99) * 1920:.2f} for 99 in 100")
  step = np.abs(first.astype(int) - last).max(-1)
  usual = np.abs(loop[1].astype(int) - loop[0]).max(-1)
  print(f"  last frame to first: {(step > 40).mean():.3%} of pixels change strongly; the loop's own first step changes {(usual > 40).mean():.3%}")
  if np.nanmean(off) * 1920 > 1.0 or strong.mean() > moved.mean() / 4:
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


def colours_of(frame):
  """The ground and the stripes' colours as this source has them: a video's are a level or two off the still's."""
  flat = frame.reshape(-1, 3).astype(np.float32)
  own = lambda colour: np.median(flat[np.abs(flat - colour).sum(-1) < 12], axis=0)
  return own(GROUND), np.array([own(stripe) for stripe in STRIPES])


def place(frame, colours):
  """The middle and the width of each stripe in each row, as shares of the width, finer than a pixel."""
  ground, stripes = colours
  colour = frame.astype(np.float32) - ground
  across = np.arange(W, dtype=np.float32)
  centres, widths = [], []
  for stripe in stripes:
    way = stripe - ground
    share = (colour @ way) / (way @ way)
    away = np.abs(colour - share[..., None] * way).sum(-1)
    cover = np.where(away < 7, np.clip(share, 0, 1), 0)
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
