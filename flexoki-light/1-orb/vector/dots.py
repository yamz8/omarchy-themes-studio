# Write orb-dots.svg: every dot of the still written out as its own square.
# Usage: python dots.py still.png > orb-dots.svg
# One line per row of dots. "M1544 702h4v4h-4z" means: move to x 1544,
# y 702, draw 4 right, 4 down, 4 left, and close the square.
import sys
import numpy as np
from PIL import Image

GRID_X, GRID_Y = 0, 2

img = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(float)
H, W = img.shape
h, w = (H - GRID_Y) // 4, (W - GRID_X) // 4
dark = (img[GRID_Y:GRID_Y + 4 * h, GRID_X:GRID_X + 4 * w].reshape(h, 4, w, 4) < 128).sum((1, 3)) > 8

rows = []
for j in range(h):
  xs = np.nonzero(dark[j])[0]
  if len(xs):
    y = GRID_Y + 4 * j
    rows.append("    " + " ".join("M%d %dh4v4h-4z" % (GRID_X + 4 * i, y) for i in xs))

print('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3840 2160">')
print('  <title>Flexoki Light orb, every dot written out</title>')
print('  <!-- The same picture as orb.svg, but with no idea of a ball in it: just')
print('       %d squares of ink, one row of dots per line. Read about.md. -->' % dark.sum())
print('  <rect width="3840" height="2160" fill="#FFFCF0"/>')
print('  <path fill="#100F0F" d="')
print("\n".join(rows))
print('  "/>')
print('</svg>')
