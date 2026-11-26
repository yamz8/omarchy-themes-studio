# Totoro, as a scene

The first background tried as a scene: a description and a few small pictures that a player draws live, where today a video is played. Catppuccin's Totoro was picked because it already ships an intro and a loop as video, so the same motion can be compared both ways, and because its flat art is easy to cut.

## What is here

| File | What it is |
| --- | --- |
| `scene.jsonc` | The scene: which pieces move and how. Written to be changed by hand |
| `cut.py` | Cuts the pieces out of the still and reads each sprite's motion from the shipped loop |
| `pieces/` | What `cut.py` wrote: a shape and a patch for each of the eleven soot sprites, for Totoro and for his whiskers, the bare circle, the eyelids, the shape of the eyes, and `motion.json` with what it measured. 648 KB |

The still and the loop are read from where Omarchy installs them, `/usr/share/omarchy/themes/catppuccin/backgrounds/`.

## What the shipped loop does

Read from the video by `cut.py`: eleven soot sprites each drift on a small path that takes 8 seconds, up to 12 pixels up and down and 5 side to side at the still's size, each starting at a different point of its path. Totoro blinks four times in the 8 seconds, his eyelids coming down from the top. Nothing else moves.

## What the shipped intro does

Measured from the video, 156 frames at 30 a second: the circle grows from nothing starting at 0.26 s and swings 21% past its size before settling. Totoro rises from a third of the screen's height below, starting at 1.1 s, and swings 8% past his place. His whiskers come in at about 2.1 s. The eleven sprites pop in one after another between 1.75 and 2.55 s, each swinging about 17% past its size.

## How a piece is made

- **A piece is a shape, not a colour.** Its picture says where the sprite is, soft edge included. The player takes the colour from the still itself, less the patch of circle behind the sprite. Put back at home over that patch, a piece is the still again, at whatever size it is drawn. An earlier try stored each sprite's colour, and at half size its edges came out up to 63 levels off.
- **No two pieces share a pixel.** Each shape stops halfway to its neighbours. `cut.py` fails if two overlap, because a patch would then cover part of a neighbour at rest.
- **Every patch is drawn before any piece.** Sprites that sit close reach into each other's room; drawn one sprite at a time, a later patch cut a notch out of an earlier sprite.
- **For arriving, the circle is a piece of its own colour with nothing on it,** and Totoro, his whiskers and the sprites sit on it. A piece that sits on another needs no patch while the other is drawn: what is behind it is then that piece, not the still.
- **Totoro's shape stops three pixels inside the circle's edge,** so that lifted above his place he carries none of the dark around the circle. Below him the circle shows, as in the intro. A first try carried him on below the edge with invented body and belly; the intro does not, and it looked wrong.
- **The eyelids are not in the still.** They are Totoro's own colour, rest just above his eyes, and only show inside the eyes' shape, so at rest nothing of them is seen.

## Tried in a throwaway player

2026-11-26, in `~/owe-scene` (branch `scene-spike`), on an Intel UHD 620 laptop at 1920x1080, on AC. The player wrote all 192 frames of the scene's 8 seconds to disk on its own clock, and each was compared with the same frame of the shipped loop.

- **At rest the scene is the still:** 24 pixels of the screen differ, by one level.
- **Every sprite follows the loop:** over all frames a sprite is 0.25 pixels from where the loop has it on average, and 1.9 at worst, on paths up to 14.5 pixels long. Ten of the eleven stay within 1.1 pixels; the lowest one is off by 0.9 on average.
- **It moves as smoothly as the loop:** the largest step between two frames is 0.46 pixels (0.58 in the loop), and from the last frame back to the first 0.21 (0.26).
- **The blinks land on the same frames:** eyes shut in the same 20 frames of 192. On the frame before and after, the lid is not at the same height as the loop's.
- **Edges are as sharp:** the steepest edges around the sprites measure 112.8 levels a pixel, 113.3 in the loop.
- **It holds its rate in real time:** 24.0 frames a second over half a minute.
- **The screen shows what the player drew:** captured from the compositor on a spare virtual screen, the picture below the bar is the player's own frame, pixel for pixel.

| What played | Renderer CPU | Memory, with GPU buffers | GPU time, renderer and compositor |
| --- | --- | --- | --- |
| The shipped loop, 3840x2160 at 24 fps | 4.1% | 813 MB | 42.6% |
| The scene at 24 fps | 1.1% | 145 MB | 13.1% |
| The scene at 12 fps | 0.5% | 143 MB | 6.4% |

On battery, read from the battery's own current and voltage over 40 seconds, two rounds in opposite order:

| What played | Watts, first round | Second round | Over the still alone |
| --- | --- | --- | --- |
| The still alone | 6.28 | 5.84 | |
| The shipped loop | 11.37 | 11.21 | about 5.2 |
| The scene at 24 fps | 7.45 | 7.14 | about 1.2 |
| The scene at 12 fps | 6.80 | 6.75 | about 0.7 |

GPU time flatters the loop here. Under the loop the GPU's clock averaged 604 MHz and peaked at its 1150 MHz limit; under the scene it never left its 300 MHz floor, so the same work shows as more time.

## The arrive part, checked the same way

All 156 frames of the scene's arrive part against the shipped intro's, then on into idle:

- **The circle** is 1.6 pixels from the intro's width on average, on a circle 616 wide. On its first frame it is 36 off: the scene starts a frame early.
- **Totoro** is 0.6 pixels from the intro's height on average over a rise of 186, and 11 at worst, around 2 s, where the intro gives him a second small twitch that one swing does not have.
- **Nine of the eleven sprites appear on the same frame** as in the intro, and two a frame early.
- **Nothing shifts when idle takes over:** the largest change in any pixel between the last frame of arrive and the first of idle is 4 levels. The player settles the last 0.4 s of arrive into the still itself; before it did, the circle's rim shifted by a fraction of a pixel there.

## What is rough or missing

- **The whiskers fade in.** In the intro they grow outward from his face.
- **Totoro's second twitch is missing,** as above.
- **One sprite, the lowest, follows the loop less closely** than the rest. Its path in the loop is not the plain swing the scene gives it.
- **The eyelids move at a steady speed.** The loop's do not, which shows for one frame at each end of a blink.
- **Nobody has watched it run.** Everything above is measured from frames.
- **The player is a spike:** no battery or animations rule, no hand-over from the shell's still, no tests.
