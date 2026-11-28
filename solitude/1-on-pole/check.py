#!/usr/bin/python
"""Compare a render of the base at rest with the still.

Usage: check.py [render]   (default out/rest.png, made by `blender -b --python build.py -- render`)

A frame of the Loop or the Intro scene, 2280 rows tall, is compared with the still's top 2280 rows.

Prints how many pixels differ and by how much. A loop's first frame and an intro's last frame must be
the still, so anything but "no pixel differs" means a render setting has drifted.
"""

import sys
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image

from cut import find_still

HERE = Path(__file__).resolve().parent


def main():
  spec = tomllib.loads((HERE / "parts.toml").read_text())
  render_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out" / "rest.png"
  still = np.asarray(Image.open(find_still(spec)).convert("RGB")).astype(np.int16)
  render = np.asarray(Image.open(render_path).convert("RGB")).astype(np.int16)
  if render.shape[0] == still.shape[0] - 1:
    still = still[:-1]  # a frame of the Loop or Intro: the still's top rows, an even height for video
  if render.shape != still.shape:
    sys.exit(f"The render is {render.shape[1]} x {render.shape[0]}, the still {still.shape[1]} x {still.shape[0]}.")
  off = np.abs(render - still).max(axis=2)
  total = off.size
  if off.max() == 0:
    print(f"No pixel differs: the base at rest is the still ({still.shape[1]} x {still.shape[0]}).")
    return
  print(f"{np.count_nonzero(off)} of {total} pixels differ ({100 * np.count_nonzero(off) / total:.3f}%), by up to {off.max()} levels.")
  for level in (1, 2, 4, 8):
    print(f"  off by more than {level}: {np.count_nonzero(off > level)}")
  sys.exit(1)


if __name__ == "__main__":
  main()
