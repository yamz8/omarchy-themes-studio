# Rosé Pine, funky shapes

The still is a collage of flat shapes (two pink, two teal and two lavender that let each other show through, and a white one) with line art drawn on them: rings, stripes, dashes and thin lines. In the shipped loop each shape breathes, growing and shrinking by up to 3% about the place where it meets the edge of the picture, each a little behind the one before it, over 14 seconds. Line art goes with the shape it is drawn on.

This scene follows that motion closely, but it is **not ready to stand in for the loop**: it costs too much to draw (see below), because the scene format has no way to hold the picture as layers, so the scene has to work the layers out again for every pixel of every frame.

| | Shipped loop | Scene |
|---|---|---|
| Size | 7,882,808 bytes | 14,347 bytes (scene file and one shader) |
| Follows the still at rest | first frame 1.9 levels off the still (the video's colour) | exact |

## How it works

Nothing is cut out of the still. One effect of the scene's own, `effects/breathe.glsl`, works on the whole picture and reads the shapes out of the still's colours:

- Seven flat colours are every way the pink, teal and lavender lie over the ground and each other. A place in one of those colours is made of those shapes.
- A colour between two of them is the soft edge of a shape, if the flat places round it differ by that shape. If they are all the same it is line art, and what is under it is read from them.
- Line art rides on a shape, told by what it is and where: the dark dashes on the first pink shape (ten of them, which touch the rings in the top left corner, go with the rings), the white dashes on the lower teal shape, and rings, stripes and lines on the top left lavender shape or the lower right pink one.
- For each shape the shader asks what that shape has brought to this pixel, and puts the picture together again from the answers.

The motion itself (how much, each shape's lag, where each is anchored, nothing moving at the picture's edges) is the loop's, and was confirmed against the loop: each of the 25 dark dashes in the loop is within 0.3 px, at the loop's full size, of where this motion puts it.

## How close it is

`check.py` draws all 336 frames with the real player's frame tool at 960x576 and compares them with the loop:

- At rest the scene is the still as the player draws it, exactly.
- The loop moves 10.7% of the picture by more than 12 levels on average, 15.7% at its most. The scene is that far from the loop over 1.93% of the picture on average, 2.16% on its worst frame.
- The dark dashes are 0.14 px from the loop's on average, 0.20 px at worst.
- The scene's largest step between frames is 0.12 levels (the loop's is 0.43, with its video grain), and from its last frame to its first it steps 0.05 levels.

What the remaining 2% is, at the middle of the cycle:

- **The top stripe, 0.4%.** The loop loses its top stripe mid-cycle and brings it back at the ends: where the stripe lies on lavender it was too faint to be picked up as line art when the loop was made. The scene keeps the stripe and moves it with the others. This is the loop's flaw, not copied.
- **Part of the bottom thin line, 0.1%**, for the same reason: the loop drops the left end of it mid-cycle.
- **One-pixel rims, about 1.5%**, round rings, dashes and stripes: the loop's line art was lifted from a smaller source and is a little softer and wider than the still's.

Things in the scene that are wrong and the loop does not have, all small, seen in close-ups at 1920 wide:

- Light flecks along the top edge of the first pink shape where the rings cross it, and a pale sliver where the third stripe meets the edge of the lavender shape. The shader cannot know what is under line art that lies across an edge; it guesses from either side.
- The far ends of the top thin line break into dots.

Nobody has looked at this in motion. It needs an eye before it could be shown.

## What it costs

The shader is far heavier than a video. Drawn offline at the laptop's screen size (2400x1350, Intel UHD 620), a frame takes about 25 ms longer than a frame of the Latte scene mid-cycle and about 34 ms longer near the ends of the cycle (medians of five runs; Latte's own shader measured about 4 ms a frame live). At 24 frames a second that is most of the graphics chip's time. It has not been run live, and should not ship like this.

The shader has also only been compiled for desktop OpenGL (what the frame tool uses here). It is written to be valid for OpenGL ES 3.0 as well, but that has not been tried.

## What the scene format lacks for this picture

This loop is seven layers that scale, with line art that goes with them. A scene could say that in a few lines and draw it for almost nothing, but for three things:

1. **A piece's size cannot swing.** `x` and `y` take swing and pulse; `size` and `fade` only take `from`. Breathing is a swing of size. A piece also grows about its own middle, with no way to name another point; that part can be made up with `x` and `y`.
2. **Pieces cannot overlap or show through.** No two pieces may share a pixel, and a piece takes its colour from the still at home, so a pink shape moving over a lavender one keeps the colour it had where it was. This picture needs pieces with a colour of their own that mix where they overlap (multiply, here), drawn in order.
3. **An effect is given one shape and nothing else.** A shader of the scene's own gets the still and one grey mask, and the mask is also how much of its answer is kept, so it cannot carry anything else. Given the layers as pictures (or even one picture saying which shape owns each pixel) this shader would be a few texture reads. Without them it has to find the layers again from colours, which is where the cost and the flaws come from.

Two smaller things met on the way:

- Effects on areas whose rectangles overlap do not add up: each redraws its whole rectangle from the still, so the later one undoes the earlier one wherever its own shape is empty. One area per shape was the first idea here and this ruled it out. (The Nord scene's sky and sea rectangles overlap in a thin band and have the same problem there.)
- A scene has at most eight areas; this picture has seven shapes and would have used all of them.
