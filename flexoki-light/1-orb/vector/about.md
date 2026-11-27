# The Flexoki Light orb as a vector picture

This folder holds the Flexoki Light background `1-orb` (the dark dotted ball on cream paper) rebuilt as drawing instructions instead of pixels, plus a version of it that moves.

| File | What it is |
| --- | --- |
| `orb.svg` | The still. The orb described as what it is: an outline, a shading, and a pattern that turns the shading into dots. 3,582 bytes. |
| `orb-animated.svg` | The same, plus one line that makes the shading circle the ball every 8 seconds. 4,040 bytes. |
| `orb-dots.svg` | For comparison: the still with every one of its 8,344 dots written out as its own square. 153,273 bytes. |
| `measure.py`, `fit.py`, `compare.py`, `dots.py` | The small scripts used to measure the original picture, find the numbers in `orb.svg`, check the result, and write `orb-dots.svg`. |

## What a vector file is

A pixel picture, like the original `1-orb.webp`, is a grid of 3840 by 2160 coloured squares, and the file stores (in compressed form) the colour of each one. It knows nothing about what is in the picture: to the file, the orb is just a patch of dark squares.

A vector picture is a list of drawing instructions: "fill the page with cream", "here is a circle of this size", "shade it like this". The browser carries out the instructions every time it shows the picture, at whatever size the window is. The file is plain text, so you can read it and change it in any text editor.

`orb.svg` is written in SVG, the vector format browsers understand. Everything that makes the orb is in these few groups of lines.

The shading, which says how much ink each point of the ball gets (1 is solid ink, 0 is none). It is darkest at a point up and to the left of the ball's centre and fades out in a circle 670 pixels across, so the ball looks lit from the lower right:

```svg
<radialGradient id="shading" gradientUnits="userSpaceOnUse" cx="-126" cy="-281" r="670">
  <stop offset="0" stop-opacity="1"/>
  <stop offset="0.25" stop-opacity="0.75"/>
  <stop offset="0.5" stop-opacity="0.43"/>
  <stop offset="0.75" stop-opacity="0"/>
</radialGradient>
```

The outline, a circle squashed a little (366 by 331 pixels in radius) and tilted by 29 degrees:

```svg
<clipPath id="outline">
  <ellipse rx="366" ry="331" transform="rotate(-29)"/>
</clipPath>
```

The threshold tile, which is how the dots are made. The original picture is printed with an old trick called ordered dithering: the page is divided into 4 by 4 pixel cells, and every cell is either full ink or empty paper. Each cell has its own threshold, from a repeating 4 by 4 pattern of 16 different thresholds. Where the shading is darker than a cell's threshold, that cell gets ink. In a mid-grey area about half the cells pass, in a dark area nearly all of them. The tile is written as 16 small squares, each with its threshold as its opacity (the first four of the sixteen are shown):

```svg
<pattern id="thresholds" patternUnits="userSpaceOnUse" x="0" y="2" width="16" height="16">
  <g transform="scale(4)">
    <rect x="0" y="0" width="1" height="1" fill-opacity="0.094"/>
    <rect x="1" y="0" width="1" height="1" fill-opacity="0.594"/>
    <rect x="2" y="0" width="1" height="1" fill-opacity="0.219"/>
    <rect x="3" y="0" width="1" height="1" fill-opacity="0.719"/>
    ...
```

The dither itself, an SVG filter: take the shading, subtract the threshold pattern, and wherever something is left over, paint a dot in the Flexoki ink colour `#100F0F`:

```svg
<filter id="dither" ...>
  <feImage href="#threshold-sheet" result="thresholds"/>
  <feComposite in="SourceGraphic" in2="thresholds" operator="arithmetic" k2="1" k3="-1" result="difference"/>
  <feComponentTransfer in="difference" result="dots">
    <feFuncA type="linear" slope="255"/>
  </feComponentTransfer>
  <feFlood flood-color="#100F0F"/>
  <feComposite in2="dots" operator="in"/>
</filter>
```

And finally the drawing itself: cream paper, then the ball, put at x 1899, y 1039 (pixels from the top left corner), painted with the shading, cut to the outline, and passed through the dither:

```svg
<rect width="3840" height="2160" fill="#FFFCF0"/>

<g filter="url(#dither)">
  <g transform="translate(1899 1039)">
    <rect x="-700" y="-700" width="1400" height="1400" fill="url(#shading)" clip-path="url(#outline)"/>
  </g>
</g>
```

Nothing in the file is a dot. There are a few dozen numbers in it, and the browser works out all eight thousand dots from them each time it draws the picture.

`orb-dots.svg` is the other way of writing the same picture as vectors. It has no idea of a ball, a light or a pattern in it. Each line is one row of dots, and each `M1544 902h4v4h-4z` means "move to x 1544, y 902, draw 4 right, 4 down, 4 back, and close the square". It is exact, but to change the light you would have to rewrite thousands of squares.

## How to open the files

In the browser: open Chrome and drag the file into it, or type the address `file:///home/yamz8/omarchy-themes-studio/flexoki-light/1-orb/vector/orb.svg`, or run `google-chrome-stable orb.svg` in this folder. The picture fills the window. The dots come out cleanest when the browser shows the picture at exactly half or full size; on this laptop that happens in full screen (press F11). At other window sizes the dots are still there but come out a little uneven, because each 4-pixel dot has to land on a screen with fewer pixels than the picture has.

As text: open the same file in any text editor, for example `nvim orb.svg` in a terminal, or a graphical editor. After you change something and save, reload the browser tab (Ctrl+R) to see the result.

## Five experiments

Each of these changes one thing in `orb.svg` (or `orb-animated.svg` for the last one). Copy the file first if you want to keep the original, then edit, save, and reload the browser. All five (and the variations mentioned with them) were tried in Chrome and their results checked.

1. The ink colour. Find `flood-color="#100F0F"` and change it to `flood-color="#AF3029"` (Flexoki's red). The ball is now made of red dots on the cream paper; nothing else changes. Changing `fill="#FFFCF0"` on the paper line changes the paper instead.

2. The place and the size. Find `transform="translate(1899 1039)"` and change it to `transform="translate(2600 700) scale(1.5)"`. The ball moves up and to the right and grows to one and a half times its size, but its dots stay the same small size, because the dots are made after the ball is drawn. The two numbers after `translate` are the ball's centre in pixels from the top left; `scale` is its size.

3. The dot size. In the `<pattern id="thresholds" ...>` line change `width="16" height="16"` to `width="32" height="32"`, and in the line below it change `scale(4)` to `scale(8)`. Every dot doubles to 8 by 8 pixels, and the ball looks coarser, like a newspaper photo seen from close up. The pattern is still 4 by 4 cells, now each 8 pixels wide.

4. Where the light comes from. In the `<radialGradient ...>` line, `cx="-126" cy="-281"` is the darkest point of the ball, measured from its centre (negative x is left, negative y is up). Change it to `cx="126" cy="281"`: the dark side moves to the lower right, so the ball now looks lit from the upper left. Try `cx="0" cy="0"` too: the ball is darkest in the middle and fades evenly to every edge.

5. The length of the loop. Open `orb-animated.svg` and find `dur="8s"` near the top (in the line that starts `<animateTransform`). Change it to `dur="3s"`: the light circles the ball once every 3 seconds instead of 8. Changing `to="360"` into `to="-360"` makes it go round the other way.

## The moving version

`orb-animated.svg` is `orb.svg` with one more line inside the shading:

```svg
<animateTransform attributeName="gradientTransform" type="rotate" from="0" to="360" dur="8s" repeatCount="indefinite"/>
```

It turns the shading once round the ball's centre every 8 seconds, forever. The dark side slides round the ball (to the right, down, left and back up), the dots sweep across it with it, and the outline stays where it is. At the start and at every 8 seconds the shading is exactly where it is in the still, so the loop starts on the still's view and comes back to it without a jump. Nothing else is needed: no script, nothing downloaded.

How this was checked: the animation was paused at 0, 1, 2, 3, 4, 5, 6, 7, 7.9, 8 and 16 seconds in a headless Chrome and photographed. At 0, 8 and 16 seconds the picture is identical, pixel for pixel, to the still `orb.svg`. In between, between 4,700 and 11,500 cells differ from the start (the most at 4 seconds, half way round), and the centre of the ink travels in a loop from (1847, 920) through (2031, 978), (1951, 1159), (1767, 1100) and back. At 7.9 seconds only 477 cells differ from the start, so the last frame runs smoothly into the first. A screenshot of the file left to play by itself for 3 seconds matched the paused 3-second frame within 55 cells. What was not checked: how smoothly it plays in a real window on this laptop. The browser redoes the dither for the whole picture every frame, so on a slow machine it may stutter.

The intro video in the theme does something different (the orb grows into place). That would also be easy here: an `animateTransform` on the orb's `scale` instead of on the shading.

## How close it is to the real still

The numbers come from rendering `orb.svg` in headless Chrome at 3840 by 2160 and comparing it with `1-orb.webp` cell by cell (`compare.py` does this).

What matches:

- The dot grid and the threshold pattern. The original uses 4 by 4 pixel dots starting at x 0, y 2, and the 16 thresholds in `orb.svg` were read off the original (`measure.py`): 95.6% of the original's partly dark 4 by 4 blocks follow this pattern exactly. It is a close relative of the classic Bayer pattern, with two of its rows swapped.
- Position and size: the ink spans x 1544 to 2235 and y 702 to 1245 in the original (692 by 544 pixels) and x 1544 to 2235, y 698 to 1245 in the render. The centre of the ink is at (1847, 920) in both.
- The outline: the orb's area in the two pictures overlaps by 98.4% (shared area divided by combined area).
- The dots: 8,136 of the original's 8,344 dots (97.5%) land on the same cells in the render. The render adds 160 dots where the original has paper.
- How the darkness is spread, as the share of cells that are ink in a 3 by 3 grid over the orb (original / render):

  | | left | middle | right |
  | --- | --- | --- | --- |
  | top | 33% / 32% | 76% / 76% | 27% / 27% |
  | middle | 55% / 55% | 59% / 59% | 23% / 23% |
  | bottom | 22% / 22% | 22% / 22% | 3% / 3% |

- Colours: the paper is `#FFFCF0` and the ink `#100F0F` in both.

Where it differs:

- The edge. In the original even the outline is made of whole 4 by 4 dots, so it has little stair steps. In the render the outline is a smooth curve that cuts through the dots it crosses, and some dots inside the ball are cut too where the shading crosses a threshold inside a cell. 292 of the render's cells (3.5%) are partly inked; the original has none. You only see this in an enlarged crop. With bigger dots (experiment 3) the cut dots are easier to see.
- Small irregularities. The original has a few hundred dots that no smooth shading explains, scattered mostly round the edges (it looks as if it was made from a rendered or hand-shaded image, not a clean gradient). The render has none of that, so its shading falls in slightly more regular rings.
- The lower right. In the original the ball fades out into stray dots on its lit side; in the render the last few stray dots there are cut off by the outline.
- At other sizes. The original is a fixed grid of pixels that the screen scales. The vector version is redrawn for the screen, so at window sizes that are not exactly half or full size its dots come out 1 or 2 screen pixels wide and look a little finer and lighter (about 3% less ink); `orb-dots.svg` blurs instead.

`orb-dots.svg` has none of these differences: rendered in Chrome, all 8,344 of its dots land exactly on the original's cells, and it has no extra or cut dots.

## How big the files are

| File | Bytes | Compared with the still (96,890) |
| --- | --- | --- |
| `orb.svg` | 3,582 (2,624 without its explanatory comments) | 3.7% |
| `orb-animated.svg` | 4,040 | 0.7% of the 5-second intro video (556,271) |
| `orb-dots.svg` | 153,273 (22,657 when compressed with gzip, as web servers do) | 158% |
| `1-orb.webp` (the original still) | 96,890 | |
| `intros/1-orb.mp4` (the original intro) | 556,271 | |

The shaded description is about 27 times smaller than the pixel picture, and its size does not change with the picture's size: a picture twice as wide would need the same file. Writing out every dot is bigger than the pixel picture, because a compressed pixel file is very good at "a lot of the same thing", and a list of squares is not.

## What this route cannot do

- Anything that is not a simple formula. A ball, a gradient and a pattern fit in a few dozen numbers; a photograph, brush strokes or the original's small irregularities do not. A pixel picture can hold any image at all, for a fixed cost in bytes.
- Real light and depth. The moving version turns a flat gradient round the ball; it does not model a sphere, so the shape of the shadow never changes the way a real terminator would, there is no cast shadow, no reflection, and you cannot move a camera round it. A 3D scene in Blender knows the ball is round and where the light is, and can render any of that.
- Look identical everywhere. The pixel picture looks the same in every program. This file depends on the browser carrying out the dither filter correctly. It was made for and checked in Chrome. Firefox is known not to support the part of SVG used to repeat the threshold pattern inside the filter (`feImage` pointing at an element), so it will probably show the ball without proper dots there; that was not checked. Image viewers and wallpaper programs may not support SVG filters at all.
- Cost nothing to show. The browser redraws the dots every time, and in the moving version every frame; a pixel picture is just copied to the screen.

## How the numbers were found

All the scripts run with `/usr/bin/python` and take the original still as a PNG (convert it with `magick /usr/share/omarchy/themes/flexoki-light/backgrounds/1-orb.webp still.png`).

- `python measure.py still.png` finds the dot grid and its starting point, reads the 16 thresholds off the picture, and checks how well they explain it.
- `python fit.py still.png` searches for the outline (centre, radii, tilt) and the shading (centre, radius, and the opacity at each stop) that reproduce the most dots, and prints them rounded, in the form they take in `orb.svg`. It also tried a shading with a separate focal point and a squashed, tilted shape; the search settled on a plain circle, so the simpler form is what `orb.svg` uses. It takes about ten seconds.
- `python compare.py still.png render.png` prints the comparison numbers above for any 3840 by 2160 screenshot.
- `python dots.py still.png > orb-dots.svg` writes the every-dot version.

A screenshot of an SVG at the still's size can be made with a headless Chrome that uses its own throwaway profile, for example: `google-chrome-stable --headless=new --user-data-dir=/tmp/svg-profile --force-device-scale-factor=1 --hide-scrollbars --window-size=3840,2160 --screenshot=render.png file://$PWD/orb.svg`.
