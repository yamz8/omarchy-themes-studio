"""Paint in what is behind a part: the picture it would show where nearer parts cover it.

A flat-colour print is continued the way it is made. Each hidden pixel takes the ink of the
nearest place the part shows, that ink's own colour as it drifts across the part, and the paper
grain borrowed from a clean patch of the same ink. A graded part, like the sky, has no inks to
continue, so its colour is carried sideways along each row instead.
"""

import numpy as np
from scipy import ndimage as ndi

SMALLER = 4  # colour fields are worked out on a copy this many times smaller


def paint_behind(still, ink, part, index, reach, graded, unit):
  """Part `index` as RGBA at full size: itself where it shows, painted in where it is covered.

  reach is how far under nearer parts to paint, in pixels, or None for all the way.
  unit is how many pixels of this picture make one pixel of the copy parts.toml was drawn on.
  """
  height, width = part.shape
  result = np.zeros((height, width, 4), np.uint8)
  shows = part == index
  if not shows.any():
    return result
  result[shows, :3] = still[shows]
  result[shows, 3] = 255

  if reach is None:
    box = (slice(0, height), slice(0, width))
  else:
    rows, columns = np.where(shows)
    pad = int(reach) + 4
    box = (slice(max(rows.min() - pad, 0), rows.max() + pad + 1), slice(max(columns.min() - pad, 0), columns.max() + pad + 1))
  shows, covered = shows[box], part[box] > index
  picture, inks = still[box].astype(np.float32), ink[box]

  # The rim of a part is mostly the outline of whatever covers it, so the inks to continue
  # are read a little way in.
  rim = max(1, round(4 * unit))
  core = ndi.binary_erosion(shows, iterations=rim)
  if not core.any():
    core = shows
  distance, nearest = ndi.distance_transform_edt(~core, return_indices=True)
  distance -= rim
  wanted = covered if reach is None else covered & (distance <= reach)
  if not wanted.any():
    return result

  painted = np.zeros(picture.shape, np.float32)
  if graded:
    field = colour_field(picture, core, 5 * unit, 240 * unit, enough=0.02)
    painted[wanted] = field[wanted] + grain(picture, field, core, wanted)
  else:
    continued = rounded(inks[nearest[0], nearest[1]], wanted, 3 * unit)
    for number in np.unique(continued[wanted]):
      here = wanted & (continued == number)
      source = core & (inks == number)
      field = colour_field(picture, source, 10 * unit, 10 * unit)
      painted[here] = field[here] + grain(picture, field, source, here)

  alpha = np.ones(distance.shape, np.float32)
  if reach is not None:
    alpha = np.clip((reach - distance) / (0.25 * reach), 0, 1)
  view = result[box]
  view[wanted, :3] = painted[wanted].clip(0, 255).round().astype(np.uint8)
  view[wanted, 3] = (alpha[wanted] * 255).round().astype(np.uint8)
  return result


def rounded(labels, wanted, spread):
  """The same labels with their borders rounded off, so continued inks do not meet in sharp wedges."""
  best = np.zeros(labels.shape, np.float32)
  result = labels.copy()
  for number in np.unique(labels[wanted]):
    score = ndi.gaussian_filter((labels == number).astype(np.float32), spread)
    result[wanted & (score > best)] = number
    best = np.maximum(best, score)
  return result


def colour_field(picture, source, spread_down, spread_across, enough=1e-3):
  """The colour of `source`, smoothed and carried past its edges, at every pixel.

  Where less than `enough` of the neighbourhood is source, the nearest place with enough is used.
  """
  height, width = source.shape
  pad = (-height % SMALLER, -width % SMALLER)
  weight = np.pad(source.astype(np.float32), ((0, pad[0]), (0, pad[1])))
  colour = np.pad(picture * source[..., None], ((0, pad[0]), (0, pad[1]), (0, 0)))
  small = (weight.shape[0] // SMALLER, SMALLER, weight.shape[1] // SMALLER, SMALLER)
  weight = weight.reshape(small).mean((1, 3))
  colour = colour.reshape(small + (3,)).mean((1, 3))
  spread = (spread_down / SMALLER, spread_across / SMALLER)
  weight = ndi.gaussian_filter(weight, spread)
  colour = np.dstack([ndi.gaussian_filter(colour[..., channel], spread) for channel in range(3)])
  known = weight > enough
  field = colour / np.maximum(weight, 1e-6)[..., None]
  if not known.all():
    _, (row, column) = ndi.distance_transform_edt(~known, return_indices=True)
    field = field[row, column]
  field = np.dstack([ndi.zoom(field[..., channel], SMALLER, order=1) for channel in range(3)])
  return field[:height, :width]


def grain(picture, field, source, here):
  """Paper grain for the pixels `here`, tiled from the largest clean square of `source`."""
  depth = ndi.distance_transform_cdt(source, metric="chessboard")
  half = int(depth.max()) - 1
  if half < 6:
    return 0
  row, column = np.unravel_index(depth.argmax(), depth.shape)
  window = (slice(row - half, row + half + 1), slice(column - half, column + half + 1))
  patch = picture[window] - field[window]
  patch -= patch.mean((0, 1))
  tile = np.concatenate([patch, patch[::-1]], 0)
  tile = np.concatenate([tile, tile[:, ::-1]], 1)
  rows, columns = np.where(here)
  return tile[rows % tile.shape[0], columns % tile.shape[1]]
