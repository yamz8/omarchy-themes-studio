# Fit the vector description of the orb to the still.
# Usage: python fit.py still.png
#
# The orb is described by three things, and this script finds numbers for
# each so that dithering them reproduces the still's dots as closely as it can:
#   1. its outline: an ellipse (centre, two radii, a tilt);
#   2. its shading: an SVG radial gradient (a circle: centre and radius) whose
#      opacity is the darkness, from 1 (darkest) at the centre to 0 (cream) at
#      the rim, through three stops in between. (A focal point, a squash and a
#      tilt were tried too; the fit left them at a plain circle.)
#   3. the 4x4 threshold tile measured by measure.py.
# A cell (a 4x4-pixel square) is dark when the shading at its centre is above
# the cell's threshold. The fit maximises the share of cells that agree.
import sys
import json
import numpy as np
from PIL import Image
from scipy.optimize import minimize

np.seterr(over="ignore")  # exp() of large numbers in the soft step is fine: it just means 0

TILE = np.array([[1, 9, 3, 11], [14, 6, 12, 4], [2, 10, 0, 8], [13, 5, 15, 7]])
GRID_X, GRID_Y = 0, 2

img = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(float)
H, W = img.shape
h, w = (H - GRID_Y) // 4, (W - GRID_X) // 4
cells = img[GRID_Y:GRID_Y + 4 * h, GRID_X:GRID_X + 4 * w].reshape(h, 4, w, 4).mean((1, 3)) < 128

# Only look at a window around the orb (everything else is cream).
j0, j1, i0, i1 = 160, 330, 370, 580
dark = cells[j0:j1, i0:i1].astype(float)
jj, ii = np.mgrid[j0:j1, i0:i1]
X = GRID_X + 4 * ii + 2.0
Y = GRID_Y + 4 * jj + 2.0
thr = (TILE[jj % 4, ii % 4] + 0.5) / 16


def rot(px, py, cx, cy, deg):
  a = np.radians(deg)
  dx, dy = px - cx, py - cy
  return dx * np.cos(a) + dy * np.sin(a), -dx * np.sin(a) + dy * np.cos(a)


def inside(p, soft=None):
  u, v = rot(X, Y, p["ox"], p["oy"], p["orot"])
  d = np.sqrt((u / p["orx"]) ** 2 + (v / p["ory"]) ** 2)
  if soft:
    return 1 / (1 + np.exp((d - 1) * soft))
  return (d <= 1).astype(float)


def gradient_t(p):
  # Plain circular SVG radial gradient: t = distance from centre / radius.
  return np.clip(np.hypot(X - p["gx"], Y - p["gy"]) / p["gr"], 0, 1)


STOPS = [0.0, 0.25, 0.5, 0.75, 1.0]


def shade(p):
  t = gradient_t(p)
  vals = [1.0] + [min(max(p["s%d" % k], 0), 1) for k in (1, 2, 3)] + [0.0]
  return np.interp(t, STOPS, vals)


KEYS = ["ox", "oy", "orx", "ory", "orot", "gx", "gy", "gr", "s1", "s2", "s3"]
start = dict(ox=1886, oy=1007, orx=353, ory=297, orot=-25, gx=1776, gy=753, gr=660, s1=0.76, s2=0.45, s3=0.03)


def unpack(vec):
  return dict(zip(KEYS, vec))


def loss(vec, k=40, soft=0.05):
  p = unpack(vec)
  f = shade(p) * inside(p, soft=1 / soft)
  prob = 1 / (1 + np.exp(-k * (f - thr)))
  return np.mean((prob - dark) ** 2)


def agree(p):
  pred = (shade(p) * inside(p)) > thr
  return np.mean(pred == dark), pred


def report(p):
  a, pred = agree(p)
  on = dark.astype(bool)
  hit = (pred & on).sum()
  print("still's dark cells reproduced: %d / %d (%.1f%%)" % (hit, on.sum(), 100 * hit / on.sum()))
  print("extra dark cells not in the still: %d" % (pred & ~on).sum())


if __name__ == "__main__":
  vec = np.array([start[k] for k in KEYS], float)
  for k, soft in [(25, 0.04), (60, 0.02), (120, 0.01)]:
    res = minimize(loss, vec, args=(k, soft), method="Powell", options=dict(maxiter=20000, xtol=1e-3, ftol=1e-7))
    vec = res.x
    a, pred = agree(unpack(vec))
    print("k=%d agree=%.4f" % (k, a), flush=True)
  p = unpack(vec)
  report(p)
  print(json.dumps({k: round(float(v), 3) for k, v in p.items()}))
  # The numbers written into orb.svg are rounded to be easy to read and edit.
  r = {k: round(float(v)) for k, v in p.items()}
  for k in ("s1", "s2", "s3"):
    r[k] = round(min(max(float(p[k]), 0), 1), 2)
  print("rounded:", json.dumps(r))
  report(r)
  print("in orb.svg:")
  print('  radialGradient cx="%d" cy="%d" r="%d"  stops 1, %s, %s, %s' % (
    r["gx"] - r["ox"], r["gy"] - r["oy"], r["gr"], r["s1"], r["s2"], r["s3"]))
  print('  ellipse rx="%d" ry="%d" transform="rotate(%d)"' % (r["orx"], r["ory"], r["orot"]))
  print('  translate(%d %d)' % (r["ox"], r["oy"]))
