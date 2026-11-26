#!/usr/bin/python
"""Make the shapes of the Nord black moon scene: where the stars are, and where the sea is.

Usage: cut.py [still]

Nothing is cut out of this still. Both shapes are grey pictures, white where an effect works in
full and black where the still is left alone:

  pieces/sky.png  the sky and the moon, down to the skyline. Twinkle finds the stars in it itself.
  pieces/sea.png  the water, fading out towards the shore and the horizon so nothing tears there.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
STILL = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/omarchy/themes/nord/backgrounds/0-black-moon.jpg")
WIDE = 1024  # a shape is soft, and needs far fewer pixels than the still

# Where each area sits in the still: left, top, width, height, as shares of it. scene.jsonc says the same.
SKY = (0.0, 0.0, 1.0, 0.875)
SEA = (0.26, 0.855, 0.74, 0.145)
ROUGH = 0.035  # how uneven a patch may be and still be sky


def main():
  still = Image.open(STILL).convert("RGB")
  small = still.resize((WIDE, round(WIDE * still.height / still.width)), Image.LANCZOS)
  grey = np.asarray(small.convert("L")).astype(float) / 255
  h, w = grey.shape
  ys = np.arange(h)[:, None] / h
  xs = np.arange(w)[None, :] / w
  broad = ndi.gaussian_filter(grey, 6)

  # The sky is everything above the highest peak, and below that whatever is as light and as smooth
  # as sky. The mountains stay out, rock and snow alike: snow would pass for points of light, and
  # what tells it from sky is that it is rough.
  peak, shore = 0.665, 0.87
  rough = ndi.gaussian_filter(np.abs(grey - ndi.median_filter(grey, 9)), 5)
  sky = np.where(ys < peak, 1.0, ((broad > 0.30) & (rough < ROUGH)).astype(float))
  sky[ys[:, 0] > shore] = 0
  sky = ndi.binary_opening(sky > 0.5, iterations=3)
  # Only sky that reaches the top: a smooth light slope among the peaks is not sky.
  parts, _ = ndi.label(sky)
  sky = np.isin(parts, np.unique(parts[0])[np.unique(parts[0]) > 0]).astype(float)
  sky = ndi.gaussian_filter(sky, 4)
  save("sky.png", sky, SKY, w, h)

  # The sea is the lighter water below the shore line; the sand to its left is black.
  sea = ((broad > 0.17) & (ys > 0.878)).astype(float)
  sea = ndi.binary_opening(sea > 0.5, iterations=4).astype(float)
  sea = ndi.gaussian_filter(sea, 10)
  # Still at the horizon, where the water is far away, and moving more towards the viewer.
  sea *= np.clip((ys - 0.878) / 0.07, 0, 1)
  save("sea.png", sea, SEA, w, h)


def save(name, shape, at, w, h):
  left, top, wide, tall = at
  box = shape[round(top * h):round((top + tall) * h), round(left * w):round((left + wide) * w)]
  Image.fromarray((np.clip(box, 0, 1) * 255).astype(np.uint8), "L").save(HERE / "pieces" / name, optimize=True)
  print(f"pieces/{name}: {box.shape[1]}x{box.shape[0]}, {(HERE / 'pieces' / name).stat().st_size // 1024 + 1} KB, "
        f"{(box > 0.5).mean():.0%} of its place at work")


if __name__ == "__main__":
  main()
