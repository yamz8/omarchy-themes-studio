# Lumon, united in severance

Lights run along the five lines, a light runs once round the globe's outline, and the words dim and come back. Nothing is cut out of the still and the scene has no pictures at all: three effects of its own, each on its own rectangle with no shape. It has no arrive part, so the theme's intro clip still plays.

| | Shipped loop | Scene |
|---|---|---|
| Size | 233,786 bytes | 9,462 bytes (scene file and three shaders) |

The running cost was not measured.

## How it moves

- `effects/comets.glsl`: a light on each line, left to right at 0.1565 of the width a second, each with its own tail. A light takes the line's stroke towards white and leaves a faint glow just off it.
- `effects/orbit.glsl`: one light clockwise round the oval, with a tail, coming up over a third of a second and fading out before the cycle ends.
- `effects/dim.glsl`: UNITED IN sinks to two thirds of its light as one; SEVERANCE goes down to half letter by letter and comes back the same way. A letter dims towards the ground above it.

Where the lines, the oval and the letters are comes from the still. The timings come from the shipped loop: `measure.py` prints them, and the shaders were written by hand from what it prints.

## Against the loop

`check.py` draws all 240 frames with the real player at half the still's size and compares them with the shipped loop:

- 0.010% of pixels differ strongly on average and 0.016% on the worst frame, where the loop's own motion changes 0.11% and 0.25%. At rest 0.002% differ.
- Lines: a light's head is 4.8 px of 3840 from the loop's on average, 14 px for 99 in 100. Where the loop is lit the scene's light is 0.076 of the way to white from it on average.
- Globe: lit from frame 11 to 230 in the loop and 12 to 228 in the scene. Where the loop is lit the scene's light is 0.061 of the way to white from it.
- Words: the light a letter has left is 0.005 from the loop's on average and 0.08 at worst; the lowest is 0.49 in the loop and 0.50 in the scene.

## Where it differs

- Each tail is one simple shape: a rise, a hold, a fade and an end. The loop's tails are not quite that, which is most of the 0.076.
- The two longest tails end a little short of what was measured, so that every light is off the picture when the cycle comes round and the first frame is the still.
- The stroke of the oval is taken as an even band, thinner at its ends than at its top and bottom. The glow just off a stroke is one falling curve set from a few measurements on one line, not measured all round.
- How the globe's light comes up in its first third of a second is simpler than in the loop.
