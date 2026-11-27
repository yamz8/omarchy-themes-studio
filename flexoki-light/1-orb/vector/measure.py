# Measure the dot grid of the Flexoki Light orb still.
# Usage: python measure.py still.png
# Prints the grid phase, the 4x4 threshold order and the orb's darkness field.
import sys
import numpy as np
from PIL import Image

img = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(float)
H, W = img.shape

# 1. Find the grid phase: every dot edge (a change between dark and cream
#    from one pixel to the next) falls on a cell boundary, so the most common
#    position of those edges modulo 4 is where cells start.
dark = img < 128
px = int(np.argmax(np.bincount((np.nonzero(dark[:, 1:] != dark[:, :-1])[1] + 1) % 4, minlength=4)))
py = int(np.argmax(np.bincount((np.nonzero(dark[1:] != dark[:-1])[0] + 1) % 4, minlength=4)))
print("grid phase x,y:", px, py)

# 2. One value per cell: dark (True) or cream (False).
h, w = (H - py) // 4, (W - px) // 4
cells = img[py:py + 4 * h, px:px + 4 * w].reshape(h, 4, w, 4).mean((1, 3)) < 128
yy, xx = np.nonzero(cells)
print("cells:", w, "x", h, " dark cells:", int(cells.sum()))
print("orb extent x: %d-%d  y: %d-%d" % (px + 4 * xx.min(), px + 4 * xx.max() + 3, py + 4 * yy.min(), py + 4 * yy.max() + 3))

# 3. Threshold order: group the cells into 4x4 blocks. Where the shading is
#    smooth, a position inside the block with a lower threshold turns dark
#    first, so it is dark more often in partly-dark blocks. Ranking the 16
#    positions by how often they are dark gives the threshold tile.
blocks = cells[:h // 4 * 4, :w // 4 * 4].reshape(h // 4, 4, w // 4, 4).transpose(0, 2, 1, 3)
count = blocks.sum((2, 3))
partial = (count > 0) & (count < 16)
rate = blocks[partial].mean(0)
tile = np.argsort(np.argsort(-rate.ravel())).reshape(4, 4)
print("share of partly-dark blocks where each position is dark (row = y):")
print(np.round(rate, 2))
print("threshold tile (0 = first to go dark, 15 = last):")
print(tile)

# 4. Check: if the still really is this tile applied to a darkness level,
#    a block with n dark cells has exactly the n lowest positions dark.
exact = ((tile[None] < count[partial][:, None, None]) == blocks[partial]).all((1, 2))
print("partly-dark blocks that follow the tile exactly: %d / %d (%.1f%%)" % (exact.sum(), len(exact), 100 * exact.mean()))
