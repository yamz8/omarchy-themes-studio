# Vantablack, dot hands

A swell passes over the hands from left to right once a cycle, and each dot grows as it passes and shrinks back: the small dots to about twice their radius, the large ones by a fifth. Nothing is cut out of the still. The scene is one effect of its own, `effects/swell.glsl`, on the band the hands are in, and has no arrive part, so the theme's intro clip still plays.

| | Shipped loop | Scene |
|---|---|---|
| Size | 991,272 bytes | 37,125 bytes (scene file, shader, and a 32 KB shape) |

The running cost was not measured. The shader looks at up to 24 places of the still for every pixel beside a dot, which is the part to measure first.

## How it moves

A dot is grown by looking around each place for a lit one within reach, so every dot keeps its own middle and its round edge and nothing has to know where the dots are. The swell reaches a place 0.848 + 6.385 x seconds into the cycle, x from 0 to 1 across the picture, which fits every dot in the loop to 0.007 s on average.

`cut.py` makes the shape, `pieces/dots.png`, and measures the loop: how far a dot of each size has grown at each moment of the swell's passing, written into the shader as two tables (from `effects/swell.template.glsl`).

## Against the loop

`check.py` draws all 194 frames with the real player at half the still's size and compares them with the shipped loop:

- 0.018% of pixels differ strongly on average and 0.041% on the worst frame, where the loop's own motion changes 0.19% and 0.36%. Nothing differs at rest or outside the band.
- Large dots: at its largest a dot gives 1.50 times its light at rest in the loop and 1.49 in the scene.
- Small dots: 4.87 times in the loop and 3.94 in the scene at half size; 4.89 and 4.47 at the still's own size, measured on one frame. The scene's small dots swell a little less than the loop's, by about a quarter of a pixel of the still in radius at full size and more when the picture is drawn smaller.
- The swell reaches a dot within 4 ms of the loop's on average for small dots and 7 ms for large ones.
- On the last frame no dot is more than 3% from its light at rest.

## What the format lacked

- **Two effects cannot share a place.** Small and large dots need different reaches, and the natural way to say so is two areas with two shapes. But an effect redraws its whole rectangle from the still, so the second erased the first wherever its own shape was empty. Only areas whose rectangles do not overlap can each carry an effect.
- **An effect has nothing to read but the still and its area's shape, and the shape also weights the mix.** To get round the first point the one shape carries the kind: white round small dots, mid grey round large ones. The shader reads the grey to choose the reach, and returns a colour that much further from the still so that the player's mix by the same grey lands where it should. This leans on the mix not being clamped before it is written.
