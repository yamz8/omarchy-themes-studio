# Flexoki Light, orb

The light travels once round the orb every 60 seconds and comes back, and the dots of its shading follow it. Nothing is cut out: one shader of the scene's own, `effects/orbit.glsl`, works out the shading for the turned light and dithers it again on the still's own grid with the still's own pattern. 7.8 KB in two files. Flexoki Light ships no loop, so there is no video to compare it with.

This scene was not made by hand. A fresh agent produced it on 2026-11-27 from the request "I'd like the light to travel slowly round the orb, so the dots shift across it, and come back to where it started. Keep the dot look exactly as it is", with only the `omarchy-make-scene` skill to go on and without seeing the Blender and vector versions beside this file. It took about ten versions of the shader and twenty minutes.

What it found in the still and built on:

- The dots are a 4x4 ordered dither: each is a 4x4-pixel cell on a fixed grid that starts 2 pixels down.
- The orb is a circle, 372 pixels in radius. Its egg look comes from the shading: the lit side fades to no dots at all, so as the light turns the visible shape turns with it.
- A one-light shading formula with six numbers fits the still's dots, with about 7% of dots disagreeing.

What holds, by the skill's checker and the agent's own measurements:

- At rest it is the still exactly, and the cycle comes round with no step.
- At the still's full size every frame is whole cells on the still's grid, with 8,341 to 8,368 dark cells against the still's 8,344.
- About 50 to 65 of some 20,000 dots flip per frame at 12 frames a second, and none flips straight back.
- The offline cost estimate says light. It has not been measured live.

What is rough:

- The shading is a fitted formula, not the artist's, so a faint diagonal streak in the still stays put while the light moves.
- The dots that disagree with the formula let go of the still over the first five seconds, a faint settling.
- When OWE stops or starts a scene it crossfades for 0.4 seconds, which on hard dots is a brief grey blend.
- Nobody has watched it play on a desktop, and whether "light goes round" is the motion wanted for this background is not decided.

`blender/` and `vector/` hold the same picture made two other ways, for comparison.
