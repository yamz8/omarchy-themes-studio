# Kanagawa, opened up

A first try at what "a theme opened up" could mean, made to think the pattern through. Rough on purpose.

The still is Hokusai's *Under the Wave off Kanagawa*, a woodblock print: flat areas of a few inks, dark blue outlines, bare paper for the foam and the cloud, and a graded sky. In Omarchy it is `kanagawa/1-kanagawa.jpg` in [omacom/omarchy-themes-backgrounds](https://github.com/omacom/omarchy-themes-backgrounds), 4335x2990, a JPEG at quality 60. The print is in the public domain; where this scan came from is not recorded here.

## What is here

| File | What it is |
| --- | --- |
| `parts.toml` | The judgment: the twelve parts of the picture, back to front, each with a rough region drawn by eye, and how far each is painted in behind |
| `open.py` | The recipe: reads the still and `parts.toml`, writes everything in `out/` |
| `behind.py` | The part of the recipe that paints in what a part would show where nearer parts cover it |
| `still.py` | Finds the still on this machine by its name and refuses a picture that is not the one `parts.toml` was drawn on |
| `painted/` | Paintings of what a part shows where it is hidden, made by hand or by any tool. They win over the recipe's own painting. Kept in git: they cannot be rebuilt |
| `tries/` | Ways of working tried on the material: a small motion from code and in Blender, and an AI service painting a hidden area |
| `out/` | The material. Not kept in git; `open.py` rebuilds it in about a minute and a half |

## What the recipe makes

| In `out/` | What it is |
| --- | --- |
| `parts/NN-name.png` | Each part, full size: itself where it shows, and painted in where nearer parts cover it. The parts overlap, so they stack like any layers |
| `1-kanagawa.ora` | The same parts as layers in one file, for Krita, GIMP and other painting programs |
| `parts.png`, `parts.json` | One flat map of where each part shows: each pixel holds its part's number |
| `inks/N-colour.png`, `inks.png` | The picture split by ink instead of by part, lightest first, and the same as one flat map |
| `areas.png` | Every connected area of one ink, numbered (red + 256 x green + 65536 x blue), for cutting the picture a different way |
| `sheet.jpg` | Everything at a glance, with the boats, spray, cloud and text taken away at the end |

## How a part is cut

Nobody traces an outline. A part's region in `parts.toml` is a loose polygon. The recipe finds every connected area of one ink, and each area goes whole to the part that holds nearly all of it, so the cut follows the print's own lines. Only an area truly shared between parts, like the paper that runs from one wave into the next, is cut along the drawn line. A nearer part then takes the thin edge it shares with the parts behind it (`edge`), because those pixels are a blend of both and would stay behind as a ghost outline.

## How a part is painted in behind

Under the parts in front of it, as far as its `reach`, a part is continued the way the print is made: each hidden pixel takes the ink of the nearest place the part shows, that ink's colour as it drifts across the part, and paper grain tiled from a clean patch of the same ink. The sky has no inks to continue (`behind = "graded"`), so its colour is carried sideways along each row, and it is painted across the whole picture.

A file `painted/<part>.png`, the still's size and clear where nothing is painted, wins over all of that: wherever the part is hidden and the file is painted, the painting is used. Where the part shows, the still always wins, so a painting cannot change the picture at rest. It does not matter what made the file.

The recipe ends by reading the parts back and stacking them one over the other. It fails unless they give the still back, pixel for pixel.

## What is rough or missing

- **The recipe's own painting works for thin edges and for the sky, not for large hidden areas.** Take the cloud or the text away and the sky closes over them. Take a boat away and the water under it is a patchwork: the continued inks meet in blobs, not in the wave's own stripes. That needs a painted file. Only the left boat has one so far.
- **A wrong cut becomes a wrong fill, and a painted file cannot mend it.** Scraps of a boat left in a wave are continued as boat-coloured patches under the boat. They are pixels the wave shows, so they also stay when the boat is taken away, painted file or not: a thin strip of hull is still there under the left boat.
- **Edges are hard.** Each pixel shows one part. The cloud fades into the sky with no line, so it is cut with a wide edge and carries a rim of sky with it.
- **Some cuts are wrong.** A few dots of spray and strokes of the wave's outline are left in the sky, the boats carry scraps of sky and water, and the signature is cut as a box.
- **Where one wave ends is a choice.** The sea is one body of water. Splitting it into great wave, front wave and right swell was a call, and a different motion may want a different one.
- **The inks are found, not named.** Nine colours by clustering; the boats' yellow did not get one of its own.
- **Not tried everywhere.** Code, Blender and one AI service have been tried, below. The `.ora` file has not been opened in Krita or GIMP, and no painted file has been made by hand.

## Tried: the far boat bobs

The same small motion, made twice from the same parts, to see what each way of working needs. Both write to `out/tries/`.

**From code** (`tries/bob-code.py`, NumPy and ffmpeg, a six-second loop at 960 wide):

- The parts stack one over the other with nothing showing through. Before they overlapped, 2.7% of the picture showed through as seams along every edge.
- Stacked at rest at 960 wide they are close to the still but not it: 1.25% of pixels are off by more than 8 levels, where a painted-in edge sits under a soft one. So each frame is built as the still plus the change the boat makes, and then the first frame is the still exactly.
- Lifted, the boat leaves no hole and no smear. Its bow shows a short painted-in tip that was never in the print.

**In Blender** (`blender -b --python tries/bob-blender.py`, every part a flat plane under a straight-down camera):

- At the still's own size, with closest-pixel textures, a 0.01 pixel filter and the Standard view (`-- exact`), the render at rest is the still: no pixel differs.
- With Blender's defaults at 960 wide it is not: softer and about 3 levels brighter, with 21.5% of pixels off by more than 8 levels. So the settings are part of the material, and the scene is saved as `out/tries/kanagawa-parts.blend`.
- Lifted, the boat leaves no gap.

Only two frames were rendered in Blender, at rest and at the top of the bob. The loop has not been played on the desktop or run through the loops repository's check.

## Tried: an AI service paints the water behind the left boat

`tries/paint-ai.py`, on 2026-11-26. `ask` writes a 1680x1260 crop of the still around the left boat and a mask of the boat grown by 14 pixels. The two went to an image service that repaints a masked area (Nano Banana 2 through Higgsfield, at its 2k size, one try), asked to take the boat away and continue the wave. `take` fits what came back and writes `painted/great-wave.png`.

- **The fill is good.** The wave's stripes, foam dots and foam fingers continue under the boat in the print's own style. The recipe's own painting there was blobs of ink with sky showing through.
- **What comes back is not the still with a hole filled.** It is the whole crop drawn again: 2400x1792, a little stretched, and off from the still by 15 levels on average pixel for pixel, though only 5 in tone. So it is lined up on matching points (823 were found), its tone is matched to the still around the mask, and only the masked area is kept.
- **Tone matching has to leave out what the service changed.** It also cleaned up scraps of boat outside the mask. Taking those for a difference in tone pulled a purple cast into the water until differences above 12 levels were left out.
- **The stack check still passes,** because the painting is only used where the great wave is hidden.
- **Everything painted went to one part.** All that is behind this boat is the great wave. Behind the far boat are the sky and the foot of Fuji, and a painting there would have to be split between them. That has not been tried.
- **What came back is not kept in git.** It is `out/tries/paint-ai-got-1.png`, 8 MB; `painted/great-wave.png`, made from it, is.
