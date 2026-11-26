#!/usr/bin/python
"""Open up the Kanagawa still: cut it into its inks and its parts, each painted in behind.

Usage: open.py [still] [out directory]

Reads parts.toml beside this file. Without a path, the still is the one this machine has installed.
Writes everything to out/ (not kept in git; run this again to rebuild it).
"""

import json
import sys
import tomllib
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
from skimage import color

from behind import paint_behind, use_painted
from still import find_still

HERE = Path(__file__).resolve().parent
INKS = 9          # colours the print is read as
SNAP_BELOW = 0.004  # a colour area smaller than this share of the picture goes whole to one part
WHOLE_SHARE = 0.85  # and so does a larger one when this much of it fell in one part
SHEET_CELL = 800


def main():
  spec = tomllib.loads((HERE / "parts.toml").read_text())
  still_path = find_still(spec, sys.argv[1] if len(sys.argv) > 1 else None)
  out = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "out"
  (out / "inks").mkdir(parents=True, exist_ok=True)
  (out / "parts").mkdir(exist_ok=True)

  still = np.asarray(Image.open(still_path).convert("RGB"))
  height, width, _ = still.shape
  names = [part["name"] for part in spec["part"]]

  ink, ink_colours = read_inks(still)
  areas = colour_areas(ink)
  part = cut_parts(spec, ink, areas, width, height)

  write_inks(out, still, ink, ink_colours)
  write_maps(out, areas, part, names, ink, ink_colours)
  write_parts(out, still, ink, part, spec)
  write_layered_file(out, still, names, still_path.stem)
  write_sheet(out, still, part, names)
  check_stack(out, still, names)
  print(f"{len(names)} parts, {len(ink_colours)} inks, {areas.max()} colour areas -> {out}")


def read_inks(still):
  """Class every pixel as one of the print's colours, ignoring paper grain and JPEG noise."""
  calm = ndi.median_filter(still, size=(5, 5, 1))
  lab = color.rgb2lab(calm.astype(np.float32) / 255).astype(np.float32)
  points = lab.reshape(-1, 3)
  sample = points[np.random.default_rng(1).choice(len(points), 80000, replace=False)]
  centres, _ = kmeans2(sample, INKS, minit="++", seed=3, iter=40)
  centres = centres[np.argsort(-centres[:, 0])]  # lightest first
  ink = np.empty(len(points), np.uint8)
  for start in range(0, len(points), 1 << 20):
    chunk = points[start:start + (1 << 20)]
    ink[start:start + len(chunk)] = ((chunk[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
  colours = (color.lab2rgb(centres[None])[0] * 255).round().astype(np.uint8)
  return ink.reshape(still.shape[:2]), colours


def colour_areas(ink):
  """Number every connected area of one ink. These are the pieces a part is built from."""
  areas = np.zeros(ink.shape, np.int32)
  count = 0
  for index in range(ink.max() + 1):
    labels, found = ndi.label(ink == index)
    areas[labels > 0] = labels[labels > 0] + count
    count += found
  return areas


def cut_parts(spec, ink, areas, width, height):
  names = [part["name"] for part in spec["part"]]
  scale = width / spec["drawn_at_width"]
  rest = next(index for index, part in enumerate(spec["part"]) if part.get("rule") == "rest")

  # Rough regions, as drawn. A later one wins where two overlap.
  rough = Image.new("L", (width, height), rest)
  for index, part in enumerate(spec["part"]):
    for region in part.get("regions", []):
      ImageDraw.Draw(rough).polygon([(x * scale, y * scale) for x, y in region], fill=index)
  part = np.asarray(rough).copy()

  # Snap: a colour area goes whole to the part that holds nearly all of it, so a drawn edge
  # never cuts a foam finger, a dot or the sky in two. Only an area truly shared between
  # parts, like the paper that runs from one wave into the next, is cut along the drawing.
  total = int(areas.max()) + 1
  size = np.bincount(areas.ravel(), minlength=total)
  votes = np.bincount(areas.ravel().astype(np.int64) * len(names) + part.ravel(), minlength=total * len(names))
  votes = votes.reshape(total, len(names))
  winner = votes.argmax(1).astype(np.uint8)
  whole = (size < SNAP_BELOW * width * height) | (votes.max(1) >= WHOLE_SHARE * np.maximum(size, 1))
  part = np.where(whole[areas], winner[areas], part).astype(np.uint8)

  # A part can also be picked out of another by ink and size, like dots of bare paper in the sky.
  area_ink = np.zeros(total, np.uint8)
  area_ink[areas.ravel()] = ink.ravel()
  for index, entry in enumerate(spec["part"]):
    if "within" in entry:
      low, high = (limit * scale * scale for limit in entry["size"])
      chosen = (winner == names.index(entry["within"])) & whole & (area_ink == entry["ink"] - 1) & (size >= low) & (size < high)
      part[chosen[areas]] = index

  # A nearer part takes the edge it shares with the parts behind it. Those few pixels are a
  # blend of both, and left behind they would show as a ghost outline once the part moves.
  for index, entry in enumerate(spec["part"]):
    edge = entry.get("edge", spec["edge"]) * scale
    rows, columns = np.where(part == index)
    if not len(rows) or edge <= 0:
      continue
    pad = int(edge) + 2
    box = (slice(max(rows.min() - pad, 0), rows.max() + pad + 1), slice(max(columns.min() - pad, 0), columns.max() + pad + 1))
    near = ndi.distance_transform_edt(part[box] != index) <= edge
    view = part[box]
    view[near & (view < index)] = index
  return part


def cut_out(picture, mask):
  """The picture where the mask is set, and clear elsewhere."""
  return Image.fromarray(np.dstack([np.where(mask[..., None], picture, 0), np.where(mask, 255, 0)]).astype(np.uint8))


def write_inks(out, still, ink, colours):
  for index, colour in enumerate(colours):
    name = f"{index + 1}-{bytes(colour).hex()}.png"
    cut_out(still, ink == index).save(out / "inks" / name, compress_level=3)


def write_parts(out, still, ink, part, spec):
  """Each part with the picture painted in where nearer parts cover it, so the parts overlap."""
  unit = still.shape[1] / spec["drawn_at_width"]
  for index, entry in enumerate(spec["part"]):
    reach = entry.get("reach", spec["reach"])
    reach = None if reach == "all" else reach * unit
    layer = paint_behind(still, ink, part, index, reach, entry.get("behind") == "graded", unit)
    # A painting of the part, by hand or by any tool, wins over the recipe wherever the part is hidden.
    painted = HERE / "painted" / f"{entry['name']}.png"
    if painted.exists():
      print(f"{entry['name']}: {use_painted(layer, part > index, painted)} hidden pixels taken from painted/{painted.name}")
    Image.fromarray(layer).save(out / "parts" / f"{index + 1:02d}-{entry['name']}.png", compress_level=3)


def write_maps(out, areas, part, names, ink, ink_colours):
  # parts.png: one flat picture, each pixel holding its part's number (see parts.json).
  flat = Image.fromarray(part, "P")
  palette = part_palette(len(names))
  flat.putpalette(palette.ravel().tolist())
  flat.save(out / "parts.png")
  (out / "parts.json").write_text(json.dumps({index: name for index, name in enumerate(names)}, indent=2) + "\n")
  # inks.png: the same for inks, shown in the inks' own colours.
  flat = Image.fromarray(ink, "P")
  flat.putpalette(ink_colours.ravel().tolist())
  flat.save(out / "inks.png")
  # areas.png: every colour area's number, as red + 256 * green + 65536 * blue.
  coded = np.dstack([areas & 255, (areas >> 8) & 255, (areas >> 16) & 255]).astype(np.uint8)
  Image.fromarray(coded).save(out / "areas.png", compress_level=3)


def write_layered_file(out, still, names, stem):
  """An OpenRaster file: every part as a layer, for Krita, GIMP and anything else that reads .ora."""
  height, width, _ = still.shape
  stack = [f'<?xml version="1.0" encoding="UTF-8"?>\n<image version="0.0.3" w="{width}" h="{height}">\n<stack>']
  with zipfile.ZipFile(out / f"{stem}.ora", "w") as ora:
    ora.writestr(zipfile.ZipInfo("mimetype"), "image/openraster", compress_type=zipfile.ZIP_STORED)
    for index in reversed(range(len(names))):  # the file lists the top layer first
      layer = Image.open(out / "parts" / f"{index + 1:02d}-{names[index]}.png")
      box = layer.getchannel("A").getbbox()
      if not box:
        continue
      path = f"data/{index + 1:02d}-{names[index]}.png"
      with ora.open(path, "w") as handle:
        layer.crop(box).save(handle, "PNG", compress_level=3)
      stack.append(f'<layer name="{names[index]}" src="{path}" x="{box[0]}" y="{box[1]}" opacity="1.0" visibility="visible"/>')
    stack.append("</stack>\n</image>\n")
    ora.writestr("stack.xml", "\n".join(stack))
    with ora.open("mergedimage.png", "w") as handle:
      Image.fromarray(still).save(handle, "PNG", compress_level=3)
    with ora.open("Thumbnails/thumbnail.png", "w") as handle:
      thumb = Image.fromarray(still)
      thumb.thumbnail((256, 256))
      thumb.save(handle, "PNG")


def part_palette(count):
  base = np.array([
    (232, 196, 160), (250, 250, 245), (150, 110, 200), (120, 130, 140), (235, 180, 30), (50, 70, 170),
    (255, 120, 200), (245, 110, 20), (60, 170, 220), (200, 50, 50), (30, 200, 140), (20, 20, 20),
  ], np.uint8)
  return np.resize(base, (max(count, 1), 3))


def write_sheet(out, still, part, names):
  """One picture to look at: the still, the part map, each part alone, and parts taken away."""
  height, width, _ = still.shape
  cell_w, cell_h = SHEET_CELL, round(SHEET_CELL * height / width)
  small = np.asarray(Image.fromarray(still).resize((cell_w, cell_h), Image.LANCZOS)).astype(np.float32)
  small_part = np.asarray(Image.fromarray(part).resize((cell_w, cell_h), Image.NEAREST))
  checker = np.indices((cell_h, cell_w)).sum(0) // 16 % 2
  backdrop = np.where(checker[..., None] == 1, 96, 120).astype(np.float32) * np.ones(3)
  palette = part_palette(len(names)).astype(np.float32)

  layers = []
  for index, name in enumerate(names):
    layer = Image.open(out / "parts" / f"{index + 1:02d}-{name}.png").convert("RGBa")  # premultiplied
    layer = np.asarray(layer.resize((cell_w, cell_h), Image.LANCZOS)).astype(np.float32)
    layers.append((layer[..., :3], layer[..., 3:] / 255))

  def stacked(leave_out=()):
    frame = np.full((cell_h, cell_w, 3), 255.0) * np.array([1, 0, 1])
    for name, (colour, alpha) in zip(names, layers):
      if name not in leave_out:
        frame = colour + frame * (1 - alpha)
    return frame

  cells = [("the still", small), ("where each part shows", 0.4 * small + 0.6 * palette[small_part])]
  for index, name in enumerate(names):
    colour, alpha = layers[index]
    cells.append((f"{index + 1:02d} {name}", colour + backdrop * (1 - alpha)))
  cells.append(("boats taken away", stacked(("boat-far", "boat-left", "boat-front"))))
  cells.append(("boats, spray, cloud, text taken away", stacked(("boat-far", "boat-left", "boat-front", "spray", "cloud", "text"))))

  columns = 4
  rows = -(-len(cells) // columns)
  label_h = 44
  sheet = Image.new("RGB", (columns * cell_w, rows * (cell_h + label_h)), (24, 24, 28))
  draw = ImageDraw.Draw(sheet)
  font = ImageFont.load_default(size=28)
  for position, (label, picture) in enumerate(cells):
    x, y = position % columns * cell_w, position // columns * (cell_h + label_h)
    sheet.paste(Image.fromarray(picture.clip(0, 255).astype(np.uint8)), (x, y + label_h))
    draw.text((x + 12, y + 6), label, fill=(230, 230, 220), font=font)
  sheet.save(out / "sheet.jpg", quality=88)


def check_stack(out, still, names):
  """The parts, read back from disk and stacked one over the other, must be the still exactly."""
  stacked = np.zeros(still.shape, np.float32)
  for index, name in enumerate(names):
    layer = np.asarray(Image.open(out / "parts" / f"{index + 1:02d}-{name}.png")).astype(np.float32)
    alpha = layer[..., 3:] / 255
    stacked = layer[..., :3] * alpha + stacked * (1 - alpha)
  if not (stacked.round().astype(np.uint8) == still).all():
    sys.exit("the parts do not stack back to the still")
  print("stack check: the parts stack back to the still, pixel for pixel")


if __name__ == "__main__":
  main()
