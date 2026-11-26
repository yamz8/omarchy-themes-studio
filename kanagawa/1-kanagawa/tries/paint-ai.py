#!/usr/bin/python
"""Try painting a large hidden area with an AI service: the water behind the left boat.

Usage: tries/paint-ai.py ask             writes the crop and the mask to send, to out/tries/
       tries/paint-ai.py take <picture>  fits what came back and writes painted/great-wave.png

Any service that repaints a masked area of a picture will do. It is asked to take the boat away
and continue the wave. What comes back is a new picture of the whole crop, close to the still
but not it, so it is lined up with the crop, its tone is matched to the still around the mask,
and only the masked area is kept. open.py then uses painted/great-wave.png wherever the great
wave is hidden.
"""

import json
import sys
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color, feature, measure, transform

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from behind import colour_field  # noqa: E402
from still import find_still  # noqa: E402

AWAY, INTO = "boat-left", "great-wave"  # the part taken away, and the part that is painted where it was
BOX = (0, 1180, 1680, 2440)  # left, top, right, bottom in the still: the boat with the wave around it, 4:3
GROW = 14  # pixels the mask reaches past the boat, to take its outline with it
TONE_LIMIT = 12  # levels: a larger difference from the still is a different drawing, not a different tone
TRIES = HERE / "out" / "tries"


def main():
  still = np.asarray(Image.open(find_still(tomllib.loads((HERE / "parts.toml").read_text()))).convert("RGB"))
  names = json.loads((HERE / "out" / "parts.json").read_text())
  number = next(int(key) for key, name in names.items() if name == AWAY)
  part = np.asarray(Image.open(HERE / "out" / "parts.png"))
  box = (slice(BOX[1], BOX[3]), slice(BOX[0], BOX[2]))
  crop = still[box]
  mask = ndi.binary_dilation(ndi.binary_fill_holes(part[box] == number), iterations=GROW)
  TRIES.mkdir(parents=True, exist_ok=True)

  if sys.argv[1:] == ["ask"]:
    Image.fromarray(crop).save(TRIES / "paint-ai-crop.png")
    Image.fromarray((mask * 255).astype(np.uint8)).save(TRIES / "paint-ai-mask.png")
    print(f"send {TRIES}/paint-ai-crop.png with paint-ai-mask.png (white is the area to repaint, {mask.mean():.1%} of the crop)")
  elif len(sys.argv) == 3 and sys.argv[1] == "take":
    take(np.asarray(Image.open(sys.argv[2]).convert("RGB")), crop, mask, still.shape, box)
  else:
    sys.exit(__doc__)


def take(got, crop, mask, shape, box):
  height, width, _ = crop.shape
  fitted, matched = line_up(got, crop, mask)
  crop = crop.astype(np.float32)
  around = ~ndi.binary_dilation(mask, iterations=3)

  def tone_off(picture):
    smooth = lambda values: np.dstack([ndi.gaussian_filter(values[..., channel], 6) for channel in range(3)])
    return np.abs(smooth(picture) - smooth(crop)).max(-1)[around].mean()

  # The service's picture is a little off in tone. Where the still shows the same thing, the
  # difference is known; it is smoothed, carried into the mask, and taken out. Where the two show
  # different things (the service also cleans up scraps of boat left outside the mask), the
  # difference is not tone and is left out.
  calm = lambda picture: np.dstack([ndi.gaussian_filter(picture[..., channel], 3) for channel in range(3)])
  same = around & (np.abs(calm(crop) - calm(fitted)).max(-1) < TONE_LIMIT)
  toned = fitted + colour_field(crop - fitted, same, 24, 24, enough=0.05).clip(-TONE_LIMIT, TONE_LIMIT)
  detail = np.abs(fitted - crop).max(-1)[around]
  print(f"lined up on {matched} matching points; around the mask the tone is off by {tone_off(fitted):.1f} levels "
        f"before matching and {tone_off(toned):.1f} after; pixel for pixel it is off by {detail.mean():.1f} "
        f"on average, so it is the same picture drawn again, not the still")

  painted = np.zeros(shape[:2] + (4,), np.uint8)
  view = painted[box]
  view[mask, :3] = toned[mask].clip(0, 255).round().astype(np.uint8)
  view[mask, 3] = 255
  (HERE / "painted").mkdir(exist_ok=True)
  Image.fromarray(painted).save(HERE / "painted" / f"{INTO}.png", optimize=True)
  print(f"wrote painted/{INTO}.png; run open.py to use it")


def line_up(got, crop, mask):
  """`got` moved and stretched onto the crop, by matching points outside the mask."""
  height, width, _ = crop.shape
  small = (width // 2, height // 2)
  grey = lambda picture: color.rgb2gray(np.asarray(Image.fromarray(picture).resize(small, Image.LANCZOS)))
  finder = feature.ORB(n_keypoints=1500, fast_threshold=0.05)
  finder.detect_and_extract(grey(crop))
  on_crop, crop_marks = finder.keypoints, finder.descriptors
  finder.detect_and_extract(grey(got))
  on_got, got_marks = finder.keypoints, finder.descriptors
  clear = ~np.asarray(Image.fromarray(mask).resize(small, Image.NEAREST))[on_crop[:, 0].astype(int), on_crop[:, 1].astype(int)]
  on_crop, crop_marks = on_crop[clear], crop_marks[clear]
  pairs = feature.match_descriptors(crop_marks, got_marks, cross_check=True)
  model, agree = measure.ransac((on_got[pairs[:, 1]][:, ::-1], on_crop[pairs[:, 0]][:, ::-1]), transform.AffineTransform,
                                min_samples=3, residual_threshold=1.5, max_trials=3000, rng=1)
  if agree.sum() < 50:
    sys.exit(f"only {agree.sum()} points of the picture match the crop; it is not a repaint of it")
  to_small = np.diag([small[0] / got.shape[1], small[1] / got.shape[0], 1])
  to_full = np.diag([width / small[0], height / small[1], 1])
  move = transform.AffineTransform(matrix=to_full @ model.params @ to_small)
  got = got.astype(np.float32)
  fitted = [transform.warp(got[..., channel], move.inverse, output_shape=(height, width), order=3, preserve_range=True) for channel in range(3)]
  return np.dstack(fitted).astype(np.float32), int(agree.sum())


if __name__ == "__main__":
  main()
