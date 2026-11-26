#!/usr/bin/python
"""Check the Vantablack scene against the loop it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part to files, with no window, at half the
still's size, and compares each with the same frame of the shipped loop: how many pixels differ,
and for every dot how much light it and its surroundings give, which is how large it is drawn.
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
THEMES = Path("/usr/share/omarchy/themes/vantablack/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
W, H, FPS, BATCH = 1728, 1117, 24, 24
TOP, BOTTOM = round(0.29 * H), round(0.71 * H)


def main():
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(THEMES / "loops" / "0-dot-hands.mp4"), "-vf", f"scale={W}:{H}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
  loop = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
  count = len(loop)
  # The dots, found in the still at its own size and brought down to this one.
  still = np.asarray(Image.open(THEMES / "0-dot-hands.webp").convert("L"))
  dots, number = ndi.label(still > 40)
  each = np.arange(1, number + 1)
  small = ndi.sum(np.ones_like(still), dots, each) < 60
  around = ndi.grey_dilation(dots, size=(9, 9))[::2, ::2][:H, :W]
  light = lambda frame: ndi.sum(frame.astype(np.float32), around, each)
  ours, theirs, strong, moved, outside = [], [], [], [], []
  for start in range(0, count, BATCH):
    some = min(BATCH, count - start)
    with tempfile.TemporaryDirectory() as out:
      subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--at", str(start / FPS), "--frames", str(some), "--fps", str(FPS),
                      "--size", f"{W}x{H}", "--ppm", "--out", out], check=True, stderr=subprocess.DEVNULL)
      for k in range(some):
        frame = np.asarray(Image.open(f"{out}/{k:04d}.ppm").convert("L"))
        ours.append(light(frame))
        theirs.append(light(loop[start + k]))
        apart = np.abs(frame.astype(int) - loop[start + k])
        strong.append((apart > 64).mean())
        moved.append((np.abs(loop[start + k].astype(int) - loop[0]) > 64).mean())
        outside.append((apart[:TOP] > 64).sum() + (apart[BOTTOM:] > 64).sum())
        if start + k == 0:
          rest = (apart > 64).mean()
  ours, theirs, strong, moved = np.array(ours), np.array(theirs), np.array(strong), np.array(moved)
  ours, theirs = ours / ours[0], theirs / theirs[0]
  print(f"{count} frames against the loop, at {W}x{H}, {number} dots:")
  print(f"  {strong.mean():.3%} of pixels differ strongly on average, {strong.max():.3%} on the worst frame, {rest:.3%} at rest, "
        f"{int(max(outside))} pixels outside the band; the loop's own motion changes {moved.mean():.3%}, {moved.max():.3%} at its furthest")
  for name, kind in (("small", small), ("large", ~small)):
    a, b = ours[:, kind], theirs[:, kind]
    print(f"  {name} dots: at its largest a dot gives {np.median(b.max(0)):.2f} times its light at rest in the loop and {np.median(a.max(0)):.2f} in the scene; "
          f"through the loop the two are {np.abs(a - b).mean():.3f} apart on average, {np.percentile(np.abs(a - b), 99):.2f} for 99 in 100")
    when = lambda v: np.array([np.average(np.arange(count), weights=np.maximum(v[:, d] - 1, 0) ** 2 + 1e-9) for d in range(v.shape[1])]) / FPS
    late = when(a) - when(b)
    print(f"    the swell reaches a dot {np.abs(late).mean() * 1000:.0f} ms from when the loop's does on average, {np.percentile(np.abs(late), 99) * 1000:.0f} ms for 99 in 100")
  step = np.abs(ours[-1] - 1).max()
  print(f"  on the last frame no dot is more than {step:.1%} from its light at rest")
  bad = np.abs(ours - theirs).mean() > 0.08 or strong.mean() > moved.mean() / 2
  if bad:
    sys.exit("the scene has drifted from the loop")
  print("the scene follows the shipped loop")


if __name__ == "__main__":
  main()
