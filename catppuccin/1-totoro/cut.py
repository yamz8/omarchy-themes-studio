#!/usr/bin/python
"""Cut the Totoro still into the pieces its scene moves, and read their motion from the shipped loop.

Usage: cut.py [out directory]

Writes one picture for each soot sprite, the patch of circle behind it, the eyelids and the
shape of the eyes, and motion.json with where each piece sits and how the shipped loop moves it.
Then it fails if two pieces share a pixel: with none shared, the pieces at home are the still.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
THEMES = Path("/usr/share/omarchy/themes")
STILL = THEMES / "catppuccin/backgrounds/1-totoro.webp"
LOOP = THEMES / "catppuccin/backgrounds/loops/1-totoro.mp4"
ROOM = 40  # pixels kept around a piece, more than it ever travels
DARK = 100  # a pixel darker than this is ink, not circle
SOFT = 5  # pixels over which a piece's shape fades out past its ink
EDGE = 3  # pixels inside the circle's edge where Totoro's own shape stops
STILL_BELOW = 0.0005  # a swing smaller than this share of the height is no motion


def main():
  out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "pieces"
  out.mkdir(parents=True, exist_ok=True)
  still = np.asarray(Image.open(STILL).convert("RGB"))
  height, width, _ = still.shape
  ink = still.mean(-1) < DARK

  # The circle is the only light thing in the picture; Totoro and the sprites are ink inside it.
  rows, columns = np.where(~ink)
  radius = (columns.max() - columns.min()) / 2
  centre = (rows.min() + radius, (columns.max() + columns.min()) / 2)
  yy, xx = np.mgrid[:height, :width]
  in_circle = np.hypot(yy - centre[0], xx - centre[1]) < radius - 8
  blobs, count = ndi.label(ink & in_circle)
  sizes = ndi.sum(ink, blobs, range(1, count + 1))
  totoro = blobs == 1 + int(np.argmax(sizes))
  sprites = [ndi.binary_fill_holes(blobs == k) for k in range(1, count + 1) if sizes[k - 1] > 150 and k != 1 + int(np.argmax(sizes))]
  sprites.sort(key=lambda blob: tuple(np.argwhere(blob).mean(0)))
  # Totoro's pupils and the marks on his belly are ink inside the circle too, but the loop leaves them where they are.
  track = follow(sprites, centre, radius)
  moving = [k for k, entry in enumerate(track) if max(entry["x"]["swing"], entry["y"]["swing"]) > STILL_BELOW]
  sprites, track = [sprites[k] for k in moving], [track[k] for k in moving]

  # The colour of the circle everywhere, carried under the ink from the clean circle around it.
  clean = ~ndi.binary_dilation(ink, iterations=6) & in_circle
  circle = carried(still.astype(np.float32), clean, 24)

  body = np.median(still[ndi.binary_erosion(totoro, iterations=20)], 0)
  # Every pixel belongs to the ink nearest it: one of the sprites, or anything else that is ink.
  marks = np.zeros(ink.shape, np.int32)
  marks[ink & in_circle] = len(sprites) + 1
  for number, blob in enumerate(sprites, 1):
    marks[blob] = number
  _, (r, c) = ndi.distance_transform_edt(marks == 0, return_indices=True)
  nearest = marks[r, c]
  pieces, claimed = [], []
  for number, blob in enumerate(sprites, 1):
    name = f"sprite-{number}"
    box = roomy(blob, height, width)
    mine = nearest == number
    # The piece is a shape, not a colour: a player takes its colour from the still, less what is
    # behind it. So the shape only has to hold all of the sprite, soft edge included. It is full
    # where the sprite is ink, fades out over the next few pixels, and stops halfway to any
    # other ink so two pieces never share a pixel.
    away = ndi.distance_transform_edt(~blob[box])
    shape = (1 - (away - 0.5) / SOFT).clip(0, 1) * mine[box]
    shape = (shape * 255).round() / 255
    seen, under = still[box].astype(np.float32), circle[box]
    save_shape(out / f"{name}.png", shape)
    # Behind it: the circle, only under the shape, so a neighbour's room is left alone.
    save(out / f"{name}-behind.png", under, shape > 0)
    claimed.append((name, box, shape > 0))
    pieces.append({"name": name, "at": spot(box, width, height), **track[number - 1]})

  # For the arrive part, the circle on its own and Totoro on it. The circle is its colour with
  # nothing on it, in the shape of a disc; behind it is the dark around it.
  away = np.hypot(yy - centre[0], xx - centre[1])
  disc = (radius - away + 0.5).clip(0, 1)
  outside = carried(still.astype(np.float32), ~ndi.binary_dilation(disc > 0, iterations=6), 24)
  # Along its rim the disc is as much there as the still says: the share that takes the dark
  # around it to the circle's colour. Where ink runs off the rim the still cannot say, and a
  # round edge stands in.
  rim = (np.abs(away - radius) < 4) & ~ndi.binary_dilation(ink & (away < radius + 2), iterations=8)
  toward = circle - outside
  share = ((still - outside) * toward).sum(-1) / np.maximum((toward * toward).sum(-1), 1)
  disc = np.where(rim, share.clip(0, 1), disc).astype(np.float32)
  box = roomy(disc > 0, height, width, room=12)
  save(out / "disc.png", circle[box], disc[box])
  save(out / "disc-behind.png", outside[box], ndi.binary_dilation(disc > 0, iterations=4)[box])
  whole = {"disc": spot(box, width, height)}
  # Totoro is everything inside his outline: his ink, and the eyes and belly it closes in. His
  # belly runs off the bottom of the circle, so the dark below the circle closes it.
  # His whiskers are the thin strokes of his ink that stand clear of his body. The intro brings
  # them in after he has settled, so they are a piece of their own.
  thick = ndi.binary_dilation(ndi.binary_opening(totoro, iterations=7), iterations=10)
  whiskers = totoro & ~thick
  parts, count = ndi.label(whiskers)
  long = [k for k in range(1, count + 1) if (parts == k).sum() > 250]
  whiskers = np.isin(parts, long)
  below = (disc == 0) & (yy > centre[0] + 0.5 * radius)
  # His sides meet the circle's edge through a few soft pixels; closing those keeps the belly in.
  figure = ndi.binary_fill_holes(ndi.binary_closing(totoro | below, iterations=8)) & (disc > 0)
  figure &= ~ndi.binary_dilation(np.any(sprites, 0), iterations=2)
  # Around the whiskers, clear of his body, is theirs. Next to his body everything stays his, so
  # no gap opens where a whisker joins him.
  theirs = ndi.binary_dilation(whiskers, iterations=SOFT + 1) & ~thick
  figure &= ~theirs
  box = roomy(figure, height, width, room=12)
  away = ndi.distance_transform_edt(~figure[box])
  shape = (1 - (away - 0.5) / SOFT).clip(0, 1) * ((nearest == len(sprites) + 1) | figure)[box]
  shape *= ~theirs[box]
  # He stops a little inside the circle's edge, so he carries none of the dark around it.
  shape *= (radius - np.hypot(yy - centre[0], xx - centre[1])[box] - EDGE).clip(0, 1)
  shape = (shape * 255).round() / 255
  save_shape(out / "totoro.png", shape)
  save(out / "totoro-behind.png", circle[box], shape > 0)
  claimed.append(("totoro", box, shape > 0))
  whole["totoro"] = spot(box, width, height)
  wbox = roomy(whiskers, height, width, room=12)
  away = ndi.distance_transform_edt(~whiskers[wbox])
  wshape = (1 - (away - 0.5) / SOFT).clip(0, 1) * (nearest == len(sprites) + 1)[wbox]
  wshape = (wshape * 255).round() / 255
  # Where Totoro's own shape reaches, a pixel is his.
  his = np.zeros(ink.shape, bool)
  his[box] = shape > 0
  wshape[his[wbox]] = 0
  save_shape(out / "whiskers.png", wshape)
  save(out / "whiskers-behind.png", circle[wbox], wshape > 0)
  whole["whiskers"] = spot(wbox, width, height)
  claimed.append(("whiskers", wbox, wshape > 0))
  # Totoro's eyes are the two large light shapes inside him. An eyelid is his own colour, the size
  # of the eyes, and only ever shows inside their shape.
  holes, count = ndi.label(ndi.binary_fill_holes(totoro) & ~ink)
  sizes = ndi.sum(np.ones_like(ink), holes, range(1, count + 1))
  eyes = np.isin(holes, 1 + np.argsort(sizes)[-2:])
  # A little wider than the eyes, so a closed lid covers their soft edge too.
  eyes = ndi.binary_fill_holes(ndi.binary_dilation(eyes, iterations=6))
  box = roomy(eyes, height, width, room=4)
  shape = ndi.gaussian_filter(eyes[box].astype(np.float32), 1.0)
  save(out / "eyes.png", np.ones(shape.shape + (3,)) * 255, shape)
  save(out / "eyelids.png", np.ones(shape.shape + (3,)) * body, np.ones(shape.shape))
  lid = (box[0].stop - box[0].start) / height

  (out / "motion.json").write_text(json.dumps({"pieces": pieces, "eyes": spot(box, width, height), "eyelid_travel": round(float(lid), 5), **whole}, indent=2) + "\n")
  check(claimed, ink.shape)
  print(f"{len(pieces)} sprites, eyes at {spot(box, width, height)} -> {out}")


def carried(picture, source, spread):
  """The colour of `source`, smoothed and carried over everything else."""
  weight = ndi.gaussian_filter(source.astype(np.float32), spread)
  colour = np.dstack([ndi.gaussian_filter(picture[..., k] * source, spread) for k in range(3)])
  known = weight > 0.02
  field = colour / np.maximum(weight, 1e-6)[..., None]
  _, (r, c) = ndi.distance_transform_edt(~known, return_indices=True)
  return field[r, c]


def roomy(mask, height, width, room=ROOM):
  rows, columns = np.where(mask)
  return (slice(max(rows.min() - room, 0), min(rows.max() + room + 1, height)), slice(max(columns.min() - room, 0), min(columns.max() + room + 1, width)))


def spot(box, width, height):
  """Left, top, width and height of a box as shares of the picture."""
  return [round(float(value), 6) for value in (box[1].start / width, box[0].start / height, (box[1].stop - box[1].start) / width, (box[0].stop - box[0].start) / height)]


def save_shape(path, alpha):
  """A piece that takes its colour from the still is only a shape: a grey picture, white where it is solid."""
  Image.fromarray((np.asarray(alpha, np.float32) * 255).round().astype(np.uint8), "L").save(path, optimize=True)


def save(path, colour, alpha):
  rgba = np.dstack([np.asarray(colour, np.float32).round().clip(0, 255), np.asarray(alpha, np.float32) * 255]).round().astype(np.uint8)
  Image.fromarray(rgba).save(path, optimize=True)


def follow(sprites, centre, radius):
  """How the shipped loop moves each sprite: a swing up and down and one side to side, as shares of the height."""
  top, left = int(centre[0] - radius), int(centre[1] - radius)
  side = int(2 * radius) // 2 * 2
  raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(LOOP), "-vf", f"crop={side}:{side}:{left}:{top}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
  frames = np.frombuffer(raw, np.uint8).reshape(-1, side, side)
  seconds = len(frames) / 24
  t = np.arange(len(frames)) / 24
  turn = 2 * np.pi * t / seconds
  result = []
  for blob in sprites:
    rows, columns = np.where(blob)
    window = (slice(rows.min() - top - 16, rows.max() - top + 17), slice(columns.min() - left - 16, columns.max() - left + 17))
    home = np.array([rows.mean() - top - window[0].start, columns.mean() - left - window[1].start])
    path = []
    for frame in frames:
      parts, count = ndi.label(frame[window] < DARK)
      spots = np.array(ndi.center_of_mass(np.ones_like(parts), parts, range(1, count + 1)))
      areas = ndi.sum(np.ones_like(parts), parts, range(1, count + 1))
      # The sprite is the blob of its own size nearest where it was.
      fit = np.hypot(*(spots - (path[-1] if path else home)).T) + 40 * np.abs(np.log(areas / blob.sum()))
      path.append(spots[fit.argmin()])
    path = np.array(path) - path[0]
    entry = {"seconds": round(seconds, 3)}
    for axis, name in ((0, "y"), (1, "x")):
      a, b = np.linalg.lstsq(np.stack([np.sin(turn), np.cos(turn) - 1], 1), path[:, axis], rcond=None)[0]
      left_over = np.abs(path[:, axis] - a * np.sin(turn) - b * (np.cos(turn) - 1)).max()
      entry[name] = {"swing": round(float(np.hypot(a, b)) / 2160, 5), "phase": round(float(np.degrees(np.arctan2(b, a))), 1), "left_over_px": round(float(left_over), 2)}
    result.append(entry)
  return result


def check(claimed, size):
  """No two pieces may share a pixel, or a patch would cover part of a neighbour at rest.

  With that, each piece put back over its patch is the still exactly, whatever size it is drawn at:
  the piece is the still less its patch.
  """
  taken = np.zeros(size, np.int32)
  for _, box, shape in claimed:
    taken[box] += shape
  if taken.max() > 1:
    sys.exit(f"{int((taken > 1).sum())} pixels belong to more than one piece")
  print("rest check: no two pieces share a pixel, so the pieces over the still are the still")


if __name__ == "__main__":
  main()
