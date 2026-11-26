# Ristretto, launch

The five stripes sway on a wave that travels down them. Nothing is cut out of the still: the scene is one effect of its own, `effects/sway.glsl`, working on the whole picture, and has no arrive part, so the theme's intro clip still plays.

| | Shipped loop | Scene |
|---|---|---|
| Size | 925,248 bytes | 4,978 bytes (scene file and shader) |

The running cost was not measured.

## How it moves

The picture is five lanes, one for each stripe, with dark ground between. The shader looks each lane up where its stripe has come from, row by row, so a stripe slides sideways whole and keeps its edges. The middle stripe stays; the pair beside it moves one way and the other; the outer pair moves further, and widens and narrows where the stripes fan out.

How far each moves at each height is not a formula. `measure.py` follows every stripe through the shipped loop by its colour, fits the shift of its middle and the change of its width at each height to one wave of the loop's length, and writes the fits into the shader as six short tables (from `effects/sway.template.glsl`). One wave of the loop's length explains the loop's motion to 0.32 px of 1920 on average. The picture is treated as the same either side of its middle, moving opposite ways.

## Against the loop

`check.py` draws all 336 frames with the real player at 960x640 and compares them with the shipped loop:

- 0.25% of pixels differ strongly on average and 0.43% on the worst frame, where the loop's own motion changes 2.8% and 4.4%. At rest 0.003% differ.
- How far each stripe's middle has moved is 0.80 px of 1920 from the loop's on average, and within 3.4 px for 99 rows in 100. By stripe, left to right: 1.01, 0.79, 0.07, 0.90, 1.21 px.
- How much a stripe's width has changed is 2.0 px of 1920 from the loop's on average, 6.0 px for 99 in 100.
- From its last frame to its first 0.003% of pixels change strongly.

## Where it differs

- Only the outer pair's width changes are carried. The inner stripes' widths change a little in the loop too, and the scene leaves them as they are.
- The two sides are averaged into one. Where the loop's left and right differ, the scene is between them.
- The largest single difference in a stripe's middle is 194 px, on some rows of some frames. It is probably where a stripe runs off the bottom of the picture and the measurement breaks down, but that was not looked into.
- Each is measured from its own first frame, because the scene and the video are scaled down from different sizes: at rest the two already measure 1.2 px apart in stripe middles.
