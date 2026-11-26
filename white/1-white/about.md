# White, the paper folds

A slow wave travels outward from the grey opening through the folds of the paper and moves each fold across its own edge. Nothing is cut out of the still: the scene is one effect of its own, `effects/folds.glsl`, working on the whole picture. It has no arrive part, so the theme's intro clip still plays.

| File | What it is |
|---|---|
| `scene.jsonc` | The scene: one area, the whole picture, and the `folds` effect with how far a fold moves (0.0056 of the height, 12 pixels of a 4K screen), how long one wave is (0.42 of the height) and how long the cycle takes (12 seconds). |
| `effects/folds.glsl` | The shader. It holds where the folds run as a formula of 45 numbers, so the scene ships no picture of that. Written by `folds.py`; the numbers are not edited by hand. |
| `folds.py` | Works out from the still how the folds run and writes the shader. Needs NumPy, SciPy and Pillow. |
| `check.py` | Draws all 288 frames with the real player and compares them with the shipped loop. |

What ships is `scene.jsonc` and `effects/folds.glsl`: 5,912 bytes, against 6,277,254 for the loop.

## How the motion is made

The loop was made by shifting every place of the still along the direction across the folds there, by an amount that depends only on how far out among the folds the place is. So a whole fold edge moves by the same amount along its length and stays smooth. The shift is `amount x (sin(turn - phase) - sin(turn))`, measured against where the wave stands at the start, so the cycle starts and ends on the still and the wave keeps one speed all the way round. Inside the opening nothing moves, and near each edge of the picture only the motion across that edge fades.

`folds.py` gets the fold coordinate from the still itself: the way the edges face around each place, turned to point away from the opening, and then the number whose slope fits those directions best. That number is smooth enough to be a formula: a sum of 45 smooth shapes is off by 0.0008 of the height on average and 0.008 at worst, against a wave 0.42 long.

A fold's hard edge goes soft when it is read between pixels by the plain blend of the four nearest, so the shader reads the still through a sharper curve wherever a fold has moved. Where nothing has moved it returns the still as it is.

## How close it is to the loop

`check.py`, 2026-11-27, both at 1920x1080:

| | |
|---|---|
| At rest | The still as the player draws it, exactly. |
| The loop's motion | 2.23 levels from its first frame on average, 3.25 at its furthest. |
| The scene's motion against the loop's | 0.25 levels apart on average, 0.30 on the worst frame. The loop's own video grain is 0.73. |
| Agreement of the two motions | 0.991 on average, 0.969 at worst (1 is the same motion). |
| Edge sharpness while moving | The scene's steepest edges are 0.981 as steep as at rest; the loop's 0.997. |
| Last frame to first | The scene steps 0.022 levels; the loop 0.137. |

Trying other values against the loop, in a NumPy model of the same motion before the shader was written, the fit was best at the amount and the wave length the scene has: a sixth more or less amount nearly doubled the difference, and a ninth more or less wave length lost the match altogether.

## Where it differs

- **Fold edges near the opening's rim are up to about two pixels from the loop's at 1920 wide**, on a motion of six. That is the worst place, around 0.36 across and 0.61 down, four seconds in. Everywhere else the difference is a pixel-wide line along the edges, from the two being resampled differently. The scene's fold coordinate was worked out afresh from the still, and near the rim, where the picture goes flat, it does not come out quite as the loop's did.
- **Moving edges are about 2% softer than in the loop.** The loop was drawn at four times its size and shrunk. The scene reads the still at the screen's own size through a sharper curve; with the plain blend it was 7% softer.
- **For the first 0.4 seconds after it starts, edges are about 4% softer.** The player brings an effect up by blending it with the still, and a blend of two pictures a fraction of a pixel apart is soft. This happens once each time the scene starts, not each cycle.

## Not checked

- What it costs to run. The shader works a 45-number formula and reads the still ten times for every pixel of the screen, 24 times a second, which is more than the Latte scene's shader does. It has only been drawn with the frame tool, never played.
- How it looks in motion to the eye. The numbers say the motion is the loop's; nobody has watched it.
- Other screen shapes. Places are shares of the still, so on a screen that is not 16:9 the picture is cropped as the still is, and the motion goes with it.
