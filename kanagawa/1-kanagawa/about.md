# Kanagawa, opened up

A first try at what "a theme opened up" could mean, made to think the pattern through. Rough on purpose.

The still is Hokusai's *Under the Wave off Kanagawa*, a woodblock print: flat areas of a few inks, dark blue outlines, bare paper for the foam and the cloud, and a graded sky. In Omarchy it is `themes/kanagawa/backgrounds/1-kanagawa.jpg`, 4335x2990, a JPEG at quality 60. The print is in the public domain; where this scan came from is not recorded here.

## What is here

| File | What it is |
| --- | --- |
| `parts.toml` | The judgment: the twelve parts of the picture, back to front, each with a rough region drawn by eye |
| `open.py` | The recipe: reads the still and `parts.toml`, writes everything in `out/` |
| `out/` | The material. Not kept in git; `open.py` rebuilds it in about a minute |

## What the recipe makes

| In `out/` | What it is |
| --- | --- |
| `parts/NN-name.png` | Each part alone, full size, clear everywhere else |
| `1-kanagawa.ora` | The same parts as layers in one file, for Krita, GIMP and other painting programs |
| `parts.png`, `parts.json` | One flat map: each pixel holds its part's number |
| `inks/N-colour.png` | The picture split by ink instead of by part, lightest first |
| `areas.png` | Every connected area of one ink, numbered (red + 256 x green + 65536 x blue), for cutting the picture a different way |
| `sheet.jpg` | Everything at a glance |

## How a part is cut

Nobody traces an outline. A part's region in `parts.toml` is a loose polygon. The recipe finds every connected area of one ink, and each area goes whole to the part most of it fell in, so the cut follows the print's own lines. Only an area truly shared between parts, like the paper that runs from one wave into the next, is cut along the drawn line.

The recipe ends by reading the parts back and stacking them. It fails unless they give the still back, pixel for pixel.

## What is rough or missing

- **Nothing is behind a part.** Lift a boat out and there is a hole. Any motion larger than a few pixels needs the hidden picture painted in.
- **Edges are hard.** Each pixel belongs to one part. The cloud fades into the sky with no line, so its lower edge comes out ragged.
- **Some cuts are wrong.** The cloud carries the tips of the wave's claws where they cross it, the boats carry a few scraps of sky and water, and the signature is cut as a box.
- **Where one wave ends is a choice.** The sea is one body of water. Splitting it into great wave, front wave and right swell was a call, and a different motion may want a different one.
- **The inks are found, not named.** Nine colours by clustering; the boats' yellow did not get one of its own.
- **Not tried everywhere.** Code and Blender have been tried, below. The `.ora` file has not been opened in Krita or GIMP, and nothing has been handed to an AI service.

## Tried: the far boat bobs

The same small motion, made twice from the same parts, to see what each way of working needs. Both write to `out/tries/`.

**From code** (`tries/bob-code.py`, NumPy and ffmpeg, a six-second loop at 960 wide):

- Stacking the parts one over the other at any size but their own leaves seams on 2.7% of the picture, because two half-covered pixels over each other do not make a covered one. The parts have to be added up instead, which layer programs do not do.
- The first frame only equalled the still once the frame was built as the still plus the change the boat makes. Built from the parts up, it was off around the boat.
- The picture behind the boat was painted in by smoothing from its surroundings. Even for a bob of 0.7% of the height, the smear shows along the hull.

**In Blender** (`blender -b --python tries/bob-blender.py`, every part a flat plane under a straight-down camera):

- At the still's own size, with closest-pixel textures, a 0.01 pixel filter and the Standard view, the render at rest is the still: no pixel differs.
- With Blender's defaults at 960 wide it is not: softer and about 3 levels brighter, with 22% of pixels off by more than 8 levels. So the settings are part of the material, and the scene is saved as `out/tries/kanagawa-parts.blend`.
- Nothing is behind the boat here either. Lifted, it leaves a dark gap.

Only two frames were rendered in Blender, at rest and at the top of the bob. Neither loop has been played on the desktop or run through the loops repository's check.
