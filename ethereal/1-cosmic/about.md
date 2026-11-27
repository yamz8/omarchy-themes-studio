# Ethereal, cosmic

The small stars across the sky slowly dim and come back, one at a time, on an 8-second cycle at 12 frames a second. One of OWE's own effects, `twinkle`, on the whole picture, with a mask that keeps it off the lit rims of the cloud ridges. 67 KB, nearly all of it the mask.

This scene was not made by hand. It is what a fresh agent produced on 2026-11-27 from the request "Make my Ethereal background move a little. The stars should twinkle softly; keep it calm", with only the `omarchy-make-scene` skill to go on, as a test of the skill. It took two attempts and about seven minutes.

- The skill's checker passes: at rest it is the still exactly, 0.11% of the picture changes, and the cycle comes round with no step.
- The first attempt passed every check too, but twinkled along the bright edges of the clouds as well as on the stars. Nothing in the skill showed that; the agent found it by cropping frames at full size. The mask in `pieces/sky.png` is its fix.
- The large haloed stars do not twinkle: the effect only picks small points.
- Nobody has watched it play. It has not been put on a desktop, and its cost was only estimated (light).
