#!/usr/bin/python
"""Check the Totoro scene against the videos it stands in for, frame by frame.

Usage: check.py [owe-render]

Has owe-render draw every frame of the scene's idle part and of its arrive part to files, with no
window, and compares each with the same frame of the shipped loop and intro: where the sprites
are, when Totoro blinks, how the circle grows, how he rises, when the sprites pop in. Prints
what it finds, and fails if the scene has drifted from the videos.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes/catppuccin/backgrounds")
RENDER = sys.argv[1] if len(sys.argv) > 1 else "owe-render"
SIZE = (1920, 1080)
X, Y, W, H = 600, 180, 720, 720  # the part of the screen the circle is in, grown as far as it swings
DARK = 100
problems = []


def main():
  motion = json.loads((HERE / "pieces" / "motion.json").read_text())
  idle(motion)
  arrive(motion)
  if problems:
    sys.exit("the scene has drifted from the videos:\n  " + "\n  ".join(problems))
  print("the scene follows the shipped loop and intro")


def expect(ok, what):
  if not ok:
    problems.append(what)


def scene_frames(part, count, fps):
  """Every frame of one part of the scene, as owe-render draws it, cut to the circle."""
  with tempfile.TemporaryDirectory() as out:
    subprocess.run([RENDER, "--scene-frame", str(HERE / "scene.jsonc"), "--part", part, "--frames", str(count), "--fps", str(fps),
                    "--size", f"{SIZE[0]}x{SIZE[1]}", "--ppm", "--out", out], check=True)
    return np.stack([np.asarray(Image.open(f"{out}/{k:04d}.ppm"))[Y:Y + H, X:X + W] for k in range(count)]).astype(int)


def video_frames(path):
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={SIZE[0]}:{SIZE[1]}:flags=bilinear,crop={W}:{H}:{X}:{Y}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
  return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(int)


def box_of(at):
  x, y, w, h = at
  return (slice(int(y * SIZE[1]) - Y, int((y + h) * SIZE[1]) - Y + 1), slice(int(x * SIZE[0]) - X, int((x + w) * SIZE[0]) - X + 1))


def sprite_blobs(frame, labels, motion):
  """The dark blob of each sprite in a frame's labelled ink: the one nearest the middle of its piece's place."""
  found = []
  for piece in motion["pieces"]:
    box = box_of(piece["at"])
    middle = ((box[0].start + box[0].stop) / 2, (box[1].start + box[1].stop) / 2)
    ids = np.unique(labels[box][labels[box] > 0])
    found.append(min(ids, key=lambda k: np.hypot(*(np.array(ndi.center_of_mass(labels == k)) - middle))))
  return found


def idle(motion):
  loop = video_frames(THEMES / "loops" / "1-totoro.mp4")
  scene = scene_frames("idle", len(loop), 24)
  count = len(loop)
  strong = np.array([(np.abs(scene[k] - loop[k]).max(-1) > 40).mean() for k in range(count)])
  moved = np.array([(np.abs(loop[k] - loop[0]).max(-1) > 40).mean() for k in range(count)])
  print(f"idle, {count} frames against the loop: {strong.mean():.3%} of pixels differ strongly on average, {strong.max():.3%} at worst; "
        f"the loop's own motion changes {moved.mean():.3%}")

  labels, _ = ndi.label(loop[0].mean(-1) < DARK)
  home = np.array([ndi.center_of_mass(labels == k) for k in sprite_blobs(loop[0], labels, motion)])

  def track(frames):
    path, last = np.zeros((len(frames), len(home), 2)), home.copy()
    for k, frame in enumerate(frames):
      parts, n = ndi.label(frame.mean(-1) < DARK)
      sizes = ndi.sum(np.ones_like(parts), parts, range(1, n + 1))
      keep = [j for j in range(1, n + 1) if 12 < sizes[j - 1] < 4000]
      spots = np.array(ndi.center_of_mass(np.ones_like(parts), parts, keep))
      for j in range(len(home)):
        path[k, j] = spots[np.hypot(*(spots - last[j]).T).argmin()]
        last[j] = path[k, j]
    return path
  ours, theirs = track(scene), track(loop)
  apart = np.hypot(*(ours - theirs).transpose(2, 0, 1))
  step = np.hypot(*np.diff(ours, axis=0).transpose(2, 0, 1)).max()
  seam = np.hypot(*(ours[0] - ours[-1]).T).max()
  print(f"  sprites: {apart.mean():.2f} px from the loop's on average, {apart.max():.2f} at worst; largest step between frames {step:.2f} px, "
        f"last frame to first {seam:.2f} px")
  expect(apart.mean() < 0.5 and apart.max() < 3, f"idle: sprites are {apart.mean():.2f} px from the loop's on average, {apart.max():.2f} at worst")
  expect(step < 1 and seam < 1, f"idle: a sprite jumps {step:.2f} px between frames, or {seam:.2f} from the last frame to the first")

  eyes = box_of(motion["eyes"])
  shut = lambda frames: (frames[:, eyes[0], eyes[1]].mean(-1) < DARK).reshape(len(frames), -1).sum(1)
  ours, theirs = shut(scene), shut(loop)
  level = (theirs.min() + theirs.max()) / 2
  differ = int(((ours > level) != (theirs > level)).sum())
  print(f"  blinks: eyes shut on {int((theirs > level).sum())} frames of the loop and {int((ours > level).sum())} of the scene, disagreeing on {differ}")
  expect(differ == 0, f"idle: the eyes are shut on {differ} frames the loop has them open, or the other way")

  still = np.asarray(Image.open(THEMES / "1-totoro.webp").convert("RGB").resize(SIZE, Image.BILINEAR)).astype(int)[Y:Y + H, X:X + W]
  rest = np.abs(scene[0] - loop[0]).max(-1)
  print(f"  at rest against the loop's first frame: {(rest > 16).mean():.3%} of pixels differ by more than 16 levels")


def arrive(motion):
  intro = video_frames(THEMES / "intros" / "1-totoro.mp4")
  count = len(intro)
  scene = scene_frames("arrive", count, 30)
  strong = np.array([(np.abs(scene[k] - intro[k]).max(-1) > 40).mean() for k in range(count)])
  print(f"arrive, {count} frames against the intro: {strong.mean():.2%} of pixels differ strongly on average, {strong.max():.2%} at worst, "
        f"{strong[-1]:.3%} on the last frame")

  def width(frames):
    light = frames.mean(-1) > DARK
    return np.array([np.ptp(np.where(l.any(0))[0]) + 1 if l.any() else 0 for l in light])
  ours, theirs = width(scene), width(intro)
  whole = (ours < W - 5) & (theirs < W - 5)
  apart = np.abs(ours - theirs)[whole]
  print(f"  circle: {apart.mean():.1f} px from the intro's width on average, {apart.max()} at worst, on a circle {theirs[-1]} px wide")
  expect(apart.mean() < 4, f"arrive: the circle is {apart.mean():.1f} px from the intro's width on average")

  labels, n = ndi.label(intro[-1].mean(-1) < DARK)
  tbox = box_of(motion["totoro"])
  sizes = ndi.sum(np.ones_like(labels), labels, range(1, n + 1))
  body = 1 + int(np.argmax([s if (labels == k + 1)[tbox].any() else 0 for k, s in enumerate(sizes)]))
  band = (slice(None), slice(tbox[1].start + 60, tbox[1].stop - 60))
  shape = (labels == body)[band].astype(np.float32)

  def heights(frames):
    """How far below his place Totoro is on each frame, by sliding his outline down until it fits."""
    out = np.full(len(frames), np.nan)
    for k, frame in enumerate(frames):
      grey = frame.mean(-1)
      if (grey > DARK).mean() < 0.3:
        continue
      ink = (grey < DARK)[band].astype(np.float32)
      best, where = -1, 0
      for d in range(-45, 400):
        moved = np.roll(shape, d, 0)
        if d > 0:
          moved[:d] = 0
        if d < 0:
          moved[d:] = 0
        score = (moved * ink).sum() / max(np.sqrt((moved * moved).sum() * (ink * ink).sum()), 1)
        if score > best:
          best, where = score, d
      if best > 0.6:
        out[k] = where
    return out
  ours, theirs = heights(scene), heights(intro)
  both = ~np.isnan(ours) & ~np.isnan(theirs)
  apart = np.abs(ours - theirs)[both]
  print(f"  Totoro: {apart.mean():.1f} px from the intro's height on average, {apart.max():.0f} at worst, on a rise of {np.nanmax(theirs):.0f} px")
  expect(apart.mean() < 2 and apart.max() < 20, f"arrive: Totoro is {apart.mean():.1f} px from the intro's height on average, {apart.max():.0f} at worst")

  def popped(frames, own):
    room = ndi.binary_dilation(own, iterations=6)
    area = np.array([(frame.mean(-1)[room] < DARK).sum() / own.sum() for frame in frames])
    rises = np.flatnonzero((area[1:] >= 0.5) & (area[:-1] < 0.5)) + 1
    return int(rises.max()) if len(rises) else -1
  late = [popped(scene, labels == k) - popped(intro, labels == k) for k in sprite_blobs(intro[-1], labels, motion)]
  print(f"  sprites: frames later (+) or earlier (-) than in the intro: {late}")
  # Sprites that sit close share the room this looks in, so a tenth of a second is as fine as it measures.
  expect(max(abs(v) for v in late) <= 3, f"arrive: a sprite pops in {max(abs(v) for v in late)} frames off the intro")


if __name__ == "__main__":
  main()
