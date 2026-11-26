# Catppuccin Latte, color fade

The still's pastel bands rise and fall on slow waves. Nothing is cut out of it: the scene is one effect of its own, `effects/waves.glsl`, working on the whole picture, and has no arrive part, so the theme's intro clip still plays.

| | Shipped loop | Scene |
|---|---|---|
| Size | 4,136,839 bytes | 1,840 bytes (scene file and shader) |
| Renderer, processor | 3.3% | 0.9% |
| Renderer, graphics | 12.5% (6.8% drawing, 5.7% decoding) | 8.8% |
| Renderer, memory with graphics buffers | 188 MB | 189 MB |

Measured on 2026-11-27 on the laptop (Intel UHD 620, 1920x1080 at scale 1.6), plugged in, each for 20 seconds at 24 frames a second. Power was not measured.

`check.py` draws all 384 frames with the real player and compares them with the shipped loop:

- At rest the scene is the still to within 1 level, and so is the loop's first frame.
- The scene's motion is 0.26 levels from the loop's on average and 0.28 on its worst frame, on a motion of 1.3 levels. The two motions agree 0.97 on average.
- Trying other values against the loop, the fit is best at the amount the scene has (0.016 of the height) and with no shift in time.
- From its last frame to its first the scene steps 0.01 levels.

The waves are the ones the loop was made with: one wave and a smaller one twice as fast move the picture up and down, a third moves it a little from side to side, and all are measured against where they stand at the start of the cycle, so the cycle starts and ends on the still.
