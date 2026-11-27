"""What the scene tools share: reading a scene file, asking OWE about it, and drawing its frames."""

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# How long one cycle of each of OWE's own effects is unless the scene says otherwise.
BUILTIN_SECONDS = {"twinkle": 6, "glow": 5, "drift": 12, "flow": 10}
NO_SCENES = """This OWE cannot draw scenes: `owe scene info` is not a command it has ({version}).
Scenes are proposed for OWE in https://github.com/omacom/owe/pull/56 and are not in a release yet.
Until an OWE with `owe scene` is installed and first on PATH, nothing here can run. Stop and tell the user."""


def stop(message):
  sys.exit(message)


def read(path):
  """A scene file as a dictionary. It is JSON with // and /* */ comments and trailing commas."""
  text, out, i, quoted = Path(path).read_text(), [], 0, False
  while i < len(text):
    c = text[i]
    if quoted:
      out.append(c)
      if c == "\\":
        out.append(text[i + 1])
        i += 1
      elif c == '"':
        quoted = False
    elif c == '"':
      quoted = True
      out.append(c)
    elif text.startswith("//", i):
      i = text.find("\n", i)
      if i < 0:
        break
      continue
    elif text.startswith("/*", i):
      i = text.find("*/", i) + 2
      continue
    else:
      out.append(c)
    i += 1
  plain = "".join(out)
  # A comma with nothing after it but a closing bracket.
  cleaned, k = [], 0
  while k < len(plain):
    if plain[k] == ",":
      rest = plain[k + 1:].lstrip()
      if rest[:1] in ("}", "]"):
        k += 1
        continue
    cleaned.append(plain[k])
    k += 1
  return json.loads("".join(cleaned))


def arguments(usage, flags):
  """The scene file and the options from the command line. `flags` maps each option to its default; True and False take no value."""
  args, found, scene = sys.argv[1:], dict(flags), None
  while args:
    word = args.pop(0)
    if word in ("-h", "--help"):
      stop(usage.strip())
    if word.startswith("--") and word[2:] in flags:
      key = word[2:]
      if isinstance(flags[key], bool):
        found[key] = True
      elif not args:
        stop(usage.strip())
      else:
        found[key] = type(flags[key])(args.pop(0)) if flags[key] is not None else args.pop(0)
    elif scene is None and not word.startswith("-"):
      scene = Path(word)
    else:
      stop(usage.strip())
  if scene is None or not scene.is_file():
    stop(usage.strip() + ("" if scene is None else f"\n\n{scene} is not a file."))
  return scene, found


def info(path, still=None):
  """What OWE says of the scene, or stop with the reason it gives."""
  if not shutil.which("owe"):
    stop("The `owe` program is not on PATH. It comes with Omarchy's wallpaper engine, OWE.")
  result = subprocess.run(["owe", "scene", "info", str(path)] + (["--still", str(still)] if still else []), capture_output=True, text=True)
  try:
    told = json.loads(result.stdout)
  except ValueError:
    version = subprocess.run(["owe", "--version"], capture_output=True, text=True).stdout.strip() or "version unknown"
    stop(NO_SCENES.format(version=version))
  if told.get("status") != "ok":
    stop(f"OWE will not play this scene: {told.get('message', 'no reason given')}")
  if not told.get("still_path"):
    stop(f"The scene's still, {told.get('still')}, was not found from where the scene is. Name it with --still.")
  if not told.get("still_matches"):
    stop(f"{told['still_path']} is not the picture this scene was made for: its SHA-256 differs from the scene's \"sha256\".")
  return told


def periods(scene, part="idle"):
  """Every length of time something in the part repeats after, in seconds."""
  found = set()
  defaults = {e["name"]: e.get("values", {}).get("seconds", 10) for e in scene.get("effects", [])}
  defaults = {**BUILTIN_SECONDS, **defaults}
  pieces = {p["name"] for p in scene.get("pieces", [])}
  for name, what in scene.get(part, {}).items():
    if not isinstance(what, dict):
      continue
    if name in pieces:
      for motion in what.values():
        if isinstance(motion, dict):
          found.update(float(motion[key]) for key in ("seconds", "every") if key in motion and ("swing" in motion or "pulse" in motion))
          if "swing" in motion and "seconds" not in motion:
            found.add(6.0)
          if "pulse" in motion and "every" not in motion:
            found.add(8.0)
    else:
      for effect, settings in what.items():
        found.add(float(settings.get("seconds", defaults.get(effect, 10))))
  return sorted(found)


def cycle(scene, part="idle"):
  """The longest of them: one look at everything the part does."""
  if part == "arrive":
    return float(scene.get("arrive", {}).get("seconds", 0))
  found = periods(scene, part)
  return max(found) if found else 0.0


def fps(scene, part="idle"):
  return int(scene.get(part, {}).get("frames_a_second", 30 if part == "arrive" else 24))


def size_for(told, wide):
  """A frame `wide` pixels across in the still's own shape, with even sides."""
  with Image.open(told["still_path"]) as still:
    w, h = still.size
  return wide - wide % 2, max(2, round(wide * h / w / 2) * 2)


def frames(path, part, times, size, settling=0.0, still=None):
  """The scene at each of `times` (seconds into the part), as arrays, drawn by OWE with no window.

  Drawn a batch at a time into a temporary folder, so a long run never holds more than a few frames on disk."""
  times = list(times)
  with tempfile.TemporaryDirectory(prefix="scene-") as out:
    for k, at in enumerate(times):
      file = f"{out}/f.ppm"
      command = ["owe", "scene", "frame", str(path), "--part", part, "--at", f"{at:.6f}", "--size", f"{size[0]}x{size[1]}", "--out", file]
      if settling:
        command += ["--settling", str(settling)]
      if still:
        command += ["--still", str(still)]
      result = subprocess.run(command, capture_output=True, text=True)
      if result.returncode != 0:
        stop(f"OWE could not draw the scene at {at:.2f}s:\n{result.stderr.strip()}")
      yield k, at, np.asarray(Image.open(file)).astype(np.int16)


def run(path, part, start, count, rate, size, still=None):
  """`count` frames one after another from `start`, at `rate` a second, as a playing scene draws them.

  A batch at a time, so a long run never holds more than a few dozen frames on disk."""
  with tempfile.TemporaryDirectory(prefix="scene-") as out:
    done = 0
    while done < count:
      batch = min(48, count - done)
      for old in Path(out).glob("*.ppm"):
        old.unlink()
      # With one frame OWE takes --out as the file itself; with more, as a folder of numbered files.
      target = f"{out}/0000.ppm" if batch == 1 else out
      command = ["owe", "scene", "frame", str(path), "--part", part, "--at", f"{start + done / rate:.6f}", "--frames", str(batch), "--fps", str(rate),
                 "--size", f"{size[0]}x{size[1]}", "--ppm", "--out", target]
      if still:
        command += ["--still", str(still)]
      result = subprocess.run(command, capture_output=True, text=True)
      if result.returncode != 0:
        stop(f"OWE could not draw the scene:\n{result.stderr.strip()}")
      for k in range(batch):
        yield done + k, start + (done + k) / rate, np.asarray(Image.open(f"{out}/{k:04d}.ppm")).astype(np.int16)
      done += batch


def levels(a, b):
  """How far apart two frames are at each pixel: the largest difference of its three colours."""
  return np.abs(a - b).max(-1)


def where(mask):
  """The box a set of pixels lies in, as shares of the picture: left, top, width, height."""
  if not mask.any():
    return None
  ys, xs = np.where(mask)
  h, w = mask.shape
  return (xs.min() / w, ys.min() / h, (xs.max() - xs.min() + 1) / w, (ys.max() - ys.min() + 1) / h)


def box_text(box):
  return "nowhere" if box is None else f"left {box[0]:.3f}, top {box[1]:.3f}, {box[2]:.3f} wide, {box[3]:.3f} tall (shares of the picture)"


def moments(span, count, part="idle"):
  """`count` moments evenly spaced through one cycle of `span` seconds, the first at its start.

  In the idle part the first is rest, and OWE brings effects up over the first 0.4 seconds; when
  the spacing is shorter than that, the later moments are taken one cycle on, where they look the same."""
  if part == "arrive":
    return [span * k / (count - 1) for k in range(count)]
  step = span / count
  later = span if step < 0.5 else 0.0
  return [0.0] + [later + step * k for k in range(1, count)]


def marked(still, changed, radius=0, boxes=()):
  """The still dimmed, with what changed in red. `radius` grows each mark so a change one pixel wide
  can still be seen when the picture is looked at small; `boxes` are numbered places drawn on top."""
  from PIL import ImageDraw, ImageFont
  base = (np.asarray(still, float) * 0.45 + 70).clip(0, 255).astype("uint8")
  marks = Image.fromarray((changed * 255).astype("uint8"))
  if radius > 0:
    marks = marks.filter(ImageFilter.MaxFilter(2 * radius + 1))
  base[np.asarray(marks) > 0] = (255, 40, 40)
  picture = Image.fromarray(base)
  if boxes:
    draw, font = ImageDraw.Draw(picture), ImageFont.load_default(size=max(16, picture.width // 60))
    for k, (x, y, w, h) in enumerate(boxes):
      draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 255, 0), width=max(2, picture.width // 640))
      draw.text((x + 6, y + 4), str(k + 1), fill=(255, 255, 0), font=font)
  return picture


def fine(changed):
  """The share of what changed that is only a pixel or two wide: marks that vanish when each is shrunk by one pixel all round."""
  if not changed.any():
    return 0.0
  kept = np.asarray(Image.fromarray((changed * 255).astype("uint8")).filter(ImageFilter.MinFilter(3))) > 0
  return 1.0 - kept.sum() / changed.sum()
