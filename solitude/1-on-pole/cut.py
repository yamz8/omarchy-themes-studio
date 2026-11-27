#!/usr/bin/python
"""Cut the 1-on-pole still into the layers parts.toml names, each filled in where nearer ones hide it.

Usage: cut.py [still] [out directory]

Without a path, the still is the one this machine has installed, checked by its SHA-256.
Writes out/parts/NN-name.png (the still's size, with alpha), out/clean.png (the picture with the
climber and the dome taken away) and out/sheet.jpg (every layer at a glance). Ends by stacking the
layers again and failing unless they give the still back, pixel for pixel.
"""

import hashlib
import os
import sys
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent


def main():
  spec = tomllib.loads((HERE / "parts.toml").read_text())
  still_path = find_still(spec, sys.argv[1] if len(sys.argv) > 1 else None)
  out = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "out"
  (out / "parts").mkdir(parents=True, exist_ok=True)

  still = np.asarray(Image.open(still_path).convert("RGB"))
  height, width, _ = still.shape
  parts = spec["part"]

  inside = {p["name"]: polygon(p["outline"], width, height) for p in parts if "outline" in p}
  hidden = np.zeros((height, width), bool)
  for mask in inside.values():
    hidden |= mask

  # What is behind the climber and the dome: the picture mirrored in from the left along each row.
  clean = mirror_fill(still, hidden)
  Image.fromarray(clean).save(out / "clean.png")

  layers = []
  for index, part in enumerate(parts):
    if "outline" in part:
      # The part's own pixels, with whatever nearer outlines hide of it mirrored in.
      nearer = np.zeros((height, width), bool)
      for later in parts[index + 1:]:
        if "outline" in later:
          nearer |= inside[later["name"]]
      colour = mirror_fill(still, nearer) if nearer.any() else still
      alpha = outline_alpha(inside[part["name"]], part["fade"])
    else:
      colour = clean
      alpha = band_alpha(part, width, height)
    layers.append((colour, alpha))
    rgba = np.dstack([colour, (alpha * 255).round().astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(out / "parts" / f"{index + 1:02d}-{part['name']}.png")

  write_sheet(out, layers, [p["name"] for p in parts])
  check_stack(out, still, [p["name"] for p in parts])
  print(f"{len(parts)} layers -> {out}")


def find_still(spec, given=None):
  """The path of the still, from `given` or from the places Omarchy keeps a theme's backgrounds."""
  theme, name = spec["still"].split("/")
  home = Path.home() / ".config" / "omarchy"
  packaged = Path(os.environ.get("OMARCHY_PACKAGED_THEMES_PATH", "/usr/share/omarchy/themes"))
  places = [Path(given)] if given else [
    packaged / theme / "backgrounds" / name,
    home / "themes" / theme / "backgrounds" / name,
    home / "backgrounds" / theme / name,
  ]
  for place in places:
    if place.is_file() and hashlib.sha256(place.read_bytes()).hexdigest() == spec["sha256"]:
      return place
  sys.exit(f"The still parts.toml was drawn on ({spec['still']}) is not at:\n  " + "\n  ".join(map(str, places)))


def polygon(points, width, height):
  mask = Image.new("L", (width, height), 0)
  ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
  return np.asarray(mask) > 0


def outline_alpha(mask, fade):
  """1 inside the outline, falling to 0 over `fade` pixels outside it."""
  distance = ndi.distance_transform_edt(~mask)
  return np.clip(1 - distance / (fade + 1), 0, 1)


def band_alpha(part, width, height):
  """1 between `top` and `bottom`, fading over `fade` pixels centred on each edge."""
  if "top" not in part:
    return np.ones((height, width))
  y = np.arange(height, dtype=np.float64)
  fade = part["fade"]
  column = np.clip((y - part["top"]) / fade + 0.5, 0, 1)
  if "bottom" in part:
    column = np.minimum(column, np.clip((part["bottom"] - y) / fade + 0.5, 0, 1))
  return np.repeat(column[:, None], width, axis=1)


def mirror_fill(picture, holes):
  """Fill each run of hole pixels in a row with the picture mirrored about the run's left end.

  Mirroring keeps the pen hatching sharp, and it meets the edge without a step, which is where a
  small motion shows what is behind. Runs that touch the left edge mirror from their right end.
  """
  filled = picture.copy()
  width = picture.shape[1]
  for y in np.flatnonzero(holes.any(axis=1)):
    row = holes[y]
    edges = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))
    for start, end in zip(edges[::2], edges[1::2]):
      offsets = np.arange(end - start)
      if start > 0:
        source = start - 1 - offsets
        source = np.abs(source)  # a run wider than what is left of it bounces off the left edge
      else:
        source = np.minimum(end + offsets, width - 1)
      filled[y, start:end] = filled[y, source]
  return filled


def composite(layers):
  result = np.zeros(layers[0][0].shape, np.float64)
  for colour, alpha in layers:
    result = alpha[..., None] * colour + (1 - alpha[..., None]) * result
  return result


def check_stack(out, still, names):
  """Read the layers back as saved and stack them: at rest they must be the still."""
  layers = []
  for index, name in enumerate(names):
    rgba = np.asarray(Image.open(out / "parts" / f"{index + 1:02d}-{name}.png")).astype(np.float64)
    layers.append((rgba[..., :3], rgba[..., 3] / 255))
  stacked = composite(layers).round().astype(np.int16)
  off = np.abs(stacked - still.astype(np.int16)).max(axis=2)
  if off.max() > 0:
    sys.exit(f"The layers do not give the still back: {np.count_nonzero(off)} pixels differ, by up to {off.max()} levels.")
  print("The layers stacked give the still back exactly.")


def write_sheet(out, layers, names, cell=640):
  """Each layer over a checkerboard, then the clean picture, in one image."""
  height, width = layers[0][0].shape[:2]
  cell_height = round(cell * height / width)
  sheet = Image.new("RGB", (cell * 3, cell_height * 2), (30, 30, 30))
  yy, xx = np.mgrid[0:height, 0:width]
  checker = np.where(((yy // 48 + xx // 48) % 2)[..., None] == 0, 200, 120).astype(np.float64)
  tiles = [(colour, alpha, name) for (colour, alpha), name in zip(layers, names)]
  for index, (colour, alpha, name) in enumerate(tiles):
    over = (alpha[..., None] * colour + (1 - alpha[..., None]) * checker).astype(np.uint8)
    tile = Image.fromarray(over).resize((cell, cell_height))
    ImageDraw.Draw(tile).text((8, 8), name, fill=(255, 60, 60))
    sheet.paste(tile, ((index % 3) * cell, (index // 3) * cell_height))
  clean = Image.open(out / "clean.png").resize((cell, cell_height))
  ImageDraw.Draw(clean).text((8, 8), "clean (behind everything)", fill=(255, 60, 60))
  sheet.paste(clean, (2 * cell, cell_height))
  sheet.save(out / "sheet.jpg", quality=88)


if __name__ == "__main__":
  main()
