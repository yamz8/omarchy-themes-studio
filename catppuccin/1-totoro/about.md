# Totoro, as a scene

The first background tried as a scene: a description and a few small pictures that a player draws live, where today a video is played. Catppuccin's Totoro was picked because it already ships an intro and a loop as video, so the same motion can be compared both ways, and because its flat art is easy to cut.

## What is here

| File | What it is |
| --- | --- |
| `scene.jsonc` | The scene: which pieces move and how. Written to be changed by hand |
| `cut.py` | Cuts the pieces out of the still and reads each sprite's motion from the shipped loop |
| `pieces/` | What `cut.py` wrote: a shape and a patch for each of the eleven soot sprites, the eyelids, the shape of the eyes, and `motion.json` with what it measured. 204 KB |

The still and the loop are read from where Omarchy installs them, `/usr/share/omarchy/themes/catppuccin/backgrounds/`.

## What the shipped loop does

Read from the video by `cut.py`: eleven soot sprites each drift on a small path that takes 8 seconds, up to 12 pixels up and down and 5 side to side at the still's size, each starting at a different point of its path. Totoro blinks four times in the 8 seconds, his eyelids coming down from the top. Nothing else moves.

## How a piece is made

- **A piece is a shape, not a colour.** Its picture says where the sprite is, soft edge included. The player takes the colour from the still itself, less the patch of circle behind the sprite. Put back at home over that patch, a piece is the still again, at whatever size it is drawn. An earlier try stored each sprite's colour, and at half size its edges came out up to 63 levels off.
- **No two pieces share a pixel.** Each shape stops halfway to its neighbours. `cut.py` fails if two overlap, because a patch would then cover part of a neighbour at rest.
- **Every patch is drawn before any piece.** Sprites that sit close reach into each other's room; drawn one sprite at a time, a later patch cut a notch out of an earlier sprite.
- **The eyelids are not in the still.** They are Totoro's own colour, rest just above his eyes, and only show inside the eyes' shape, so at rest nothing of them is seen.

## Tried in a throwaway player

2026-11-26, in `~/owe-scene` (branch `scene-spike`), on an Intel UHD 620 laptop at 1920x1080, on AC:

- **At rest the scene is the still:** 24 pixels of the screen differ, by one level.
- **Moving, it follows the shipped loop:** at four moments compared, 0.003 to 0.02% of pixels differed strongly, where the loop itself had moved 0.2 to 0.4% of them.

| What played | Renderer CPU | Memory, with GPU buffers | GPU time, renderer and compositor |
| --- | --- | --- | --- |
| The shipped loop, 3840x2160 at 24 fps | 4.1% | 813 MB | 42.6% |
| The scene at 24 fps | 1.1% | 145 MB | 13.1% |
| The scene at 12 fps | 0.5% | 143 MB | 6.4% |

## What is rough or missing

- **The arrive part is not written.** The shipped intro grows the circle from a dot, raises Totoro into it and pops the sprites in.
- **Watts were not measured** for this scene; the laptop was plugged in.
- **A moved sprite's edge is a little softer** than in the video.
- **The motion was looked at in still frames only,** at five moments. Nobody has watched it run.
- **The player is a spike:** no battery or animations rule, no hand-over from the shell's still, no tests.
