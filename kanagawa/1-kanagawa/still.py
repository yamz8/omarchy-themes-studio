"""Find the still parts.toml was drawn on, wherever this machine keeps it.

parts.toml names the still the way the theme repositories do, `<theme>/<name>`, and pins its
sha256, so a picture that was replaced under the same name is refused.
"""

import hashlib
import os
import sys
from pathlib import Path


def find_still(spec, given=None):
  """The path of the still, from `given` or from the places Omarchy keeps a theme's backgrounds."""
  theme, name = spec["still"].split("/")
  home = Path.home() / ".config" / "omarchy"
  packaged = Path(os.environ.get("OMARCHY_PACKAGED_THEMES_PATH", "/usr/share/omarchy/themes"))
  places = [Path(given)] if given else [
    packaged / theme / "backgrounds" / name,  # the omarchy-themes-backgrounds package
    home / "themes" / theme / "backgrounds" / name,  # a theme of the user's own
    home / "backgrounds" / theme / name,  # a background the user added to a theme
  ]
  for place in places:
    if place.is_file() and hashlib.sha256(place.read_bytes()).hexdigest() == spec["sha256"]:
      return place
  sys.exit(f"The still parts.toml was drawn on ({spec['still']}) is not at:\n  " + "\n  ".join(map(str, places)))
