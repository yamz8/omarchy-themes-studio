#!/usr/bin/python
"""Try the material from code: the far boat bobs on the swell, as a short loop.

Usage: tries/bob-code.py [width]

Reads out/parts/ and parts.toml. Writes out/tries/bob-code.mp4 twice over: once with the hole
behind the boat left open (shown in magenta), once with it filled from the picture around it.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.restoration import inpaint_biharmonic

HERE = Path(__file__).resolve().parent.parent
WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 960
SECONDS, FPS = 6, 24
LIFT, TILT = 0.007, 0.7  # share of the picture's height, and degrees
MOVING = "boat-far"


def main():
  names = [part["name"] for part in tomllib.loads((HERE / "parts.toml").read_text())["part"]]
  layers = [load(HERE / "out" / "parts" / f"{index + 1:02d}-{name}.png") for index, name in enumerate(names)]
  height = layers[0].shape[0]
  moving = names.index(MOVING)
  boat = layers[moving]
  rows, columns = np.where(boat[..., 3] > 0.5)
  centre = (rows.mean(), columns.mean())

  # The parts share every pixel between them, so at working size they add up to the still.
  # Stacking them one over the other instead leaves a seam along every edge, because two
  # half-covered pixels over each other do not make a covered one.
  still_frame = sum(layers)[..., :3]
  seams = stack(layers)[..., 3] < 0.98
  print(f"stacked one over the other, {seams.mean():.1%} of the picture shows through as seams")

  # Behind the boat. Where the boat only half covers a pixel, the rest of that pixel is known:
  # it is the still minus the boat's share. Only where the boat covers a pixel fully is the
  # picture behind it unknown, and that is either left open or painted in from around it.
  alpha = boat[..., 3:]
  hidden = alpha[..., 0] > 0.98
  known = (still_frame - boat[..., :3]) / np.maximum(1 - alpha, 0.02)
  painted = inpaint_biharmonic(np.where(hidden[..., None], 0, known), hidden, channel_axis=-1)
  in_front = sum(layers[moving + 1:])[..., 3:].clip(0, 1)

  (HERE / "out" / "tries").mkdir(exist_ok=True)
  for label, behind in (("open", np.where(hidden[..., None], np.array([1.0, 0, 1.0]), known)), ("filled", painted)):
    frames = []
    for number in range(SECONDS * FPS):
      phase = 2 * np.pi * number / (SECONDS * FPS)
      moved = move(boat, centre, -LIFT * height * np.sin(phase), TILT * np.sin(phase + 0.9) - TILT * np.sin(0.9))
      # Only the change is added to the still, and only where nothing in front covers it,
      # so a boat at rest gives the still back exactly.
      change = over(behind, moved) - over(behind, boat)
      frame = still_frame + (1 - in_front) * change
      frames.append((frame.clip(0, 1) * 255).round().astype(np.uint8))
    first_off = np.abs(frames[0].astype(int) - (still_frame.clip(0, 1) * 255).round().astype(int))
    print(f"{label}: first frame differs from the still by at most {first_off.max()} levels")
    encode(frames, HERE / "out" / "tries" / f"bob-code-{label}.mp4")
    Image.fromarray(frames[len(frames) // 4]).save(HERE / "out" / "tries" / f"bob-code-{label}-peak.png")


def load(path):
  """A part at working size, with colour premultiplied so its edge resizes cleanly."""
  picture = np.asarray(Image.open(path)).astype(np.float32) / 255
  picture[..., :3] *= picture[..., 3:]
  height = round(WIDTH * picture.shape[0] / picture.shape[1] / 2) * 2
  small = [np.asarray(Image.fromarray(picture[..., channel]).resize((WIDTH, height), Image.LANCZOS)) for channel in range(4)]
  return np.dstack(small).clip(0, 1)


def stack(layers):
  result = np.zeros_like(layers[0])
  for layer in layers:
    result = layer + result * (1 - layer[..., 3:])
  return result


def over(backdrop, layer):
  return layer[..., :3] + backdrop[..., :3] * (1 - layer[..., 3:])


def move(layer, centre, down, degrees):
  if down == 0 and degrees == 0:
    return layer
  angle = np.radians(degrees)
  turn = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
  offset = np.array(centre) - turn @ (np.array(centre) + np.array([down, 0]))
  return np.dstack([ndi.affine_transform(layer[..., channel], turn, offset=offset, order=3, mode="constant") for channel in range(4)]).clip(0, 1)


def encode(frames, path):
  height, width, _ = frames[0].shape
  command = [
    "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(FPS), "-i", "-",
    "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
    "-g", "9999", "-bf", "0", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-color_range", "tv",
    "-movflags", "+faststart", str(path),
  ]
  subprocess.run(command, input=b"".join(frame.tobytes() for frame in frames), check=True)
  print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KiB)")


if __name__ == "__main__":
  main()
