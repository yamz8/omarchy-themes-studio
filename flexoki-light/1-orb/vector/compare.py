# Compare a rendering of an SVG with the original still, by numbers.
# Usage: python compare.py still.png render.png
# Both must be 3840x2160. Prints where the orb is, how much of its outline
# overlaps, how the darkness is spread, and how many dots land on the same
# 4x4 cells as in the still.
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

GRID_X, GRID_Y = 0, 2


def load(path):
  return np.asarray(Image.open(path).convert("L")).astype(float)


def cells(img):
  H, W = img.shape
  h, w = (H - GRID_Y) // 4, (W - GRID_X) // 4
  block = img[GRID_Y:GRID_Y + 4 * h, GRID_X:GRID_X + 4 * w].reshape(h, 4, w, 4)
  dark_px = (block < 128).sum((1, 3))
  # dark = more than half the cell's 16 pixels are ink; mixed = some but not all
  return dark_px > 8, (dark_px > 0) & (dark_px < 16)


def region(dark):
  # The orb's area: dark cells joined up (close the gaps between dots), holes
  # filled. Its edge is the orb's outline as the eye sees it.
  r = ndimage.binary_closing(dark, structure=np.ones((5, 5)), iterations=2)
  return ndimage.binary_fill_holes(r)


a, b = load(sys.argv[1]), load(sys.argv[2])
assert a.shape == b.shape == (2160, 3840), (a.shape, b.shape)
ca, ma = cells(a)
cb, mb = cells(b)

for name, c in (("still", ca), ("render", cb)):
  ys, xs = np.nonzero(c)
  r = region(c)
  ry, rx = np.nonzero(r)
  print("%-7s dark cells %5d  orb x %d-%d y %d-%d  (%d x %d px)  centre of ink %.0f, %.0f  area %d cells" % (
    name, c.sum(), 4 * xs.min(), 4 * xs.max() + 3, GRID_Y + 4 * ys.min(), GRID_Y + 4 * ys.max() + 3,
    4 * (xs.max() - xs.min() + 1), 4 * (ys.max() - ys.min() + 1),
    4 * xs.mean() + 2, GRID_Y + 4 * ys.mean() + 2, r.sum()))

ra, rb = region(ca), region(cb)
print("outline overlap (shared area / combined area): %.1f%%" % (100 * (ra & rb).sum() / (ra | rb).sum()))
same = (ca & cb).sum()
print("still's dots that land on the same cell in the render: %d / %d (%.1f%%)" % (same, ca.sum(), 100 * same / ca.sum()))
print("render dots on cells that are cream in the still: %d" % (cb & ~ca).sum())
print("cells only partly inked: still %d, render %d" % (ma.sum(), mb.sum()))

# Darkness spread: share of cells that are ink in a 3 x 3 grid over the
# still's orb box.
ys, xs = np.nonzero(ca)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
print("share of ink cells, 3x3 grid over the orb box (still / render):")
for gy in range(3):
  row = []
  for gx in range(3):
    sl = (slice(y0 + (y1 - y0) * gy // 3, y0 + (y1 - y0) * (gy + 1) // 3),
          slice(x0 + (x1 - x0) * gx // 3, x0 + (x1 - x0) * (gx + 1) // 3))
    row.append("%3.0f%% / %3.0f%%" % (100 * ca[sl].mean(), 100 * cb[sl].mean()))
  print("  " + "   ".join(row))

# Pixel colours away from the orb.
print("paper colour still %s render %s" % (
  np.asarray(Image.open(sys.argv[1]).convert("RGB"))[50, 50], np.asarray(Image.open(sys.argv[2]).convert("RGB"))[50, 50]))
