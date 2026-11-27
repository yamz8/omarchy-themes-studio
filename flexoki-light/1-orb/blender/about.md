# The Flexoki orb in Blender

This folder rebuilds one Omarchy background, Flexoki Light's `1-orb`, as a small 3D scene in Blender and animates it. It is meant as a first look at how Blender works: the file is small, everything in it has a plain name, and the whole scene is made by one readable Python script, so you can break things freely and get them back.

What is here:

- `build.py` makes the whole scene from nothing and saves it as `orb.blend`.
- `orb.blend` is the scene, ready to open.
- `render.sh` turns the scene into pictures: `./render.sh still` renders the first frame, `./render.sh preview` renders the whole loop as a small video. Both write into a `renders/` folder next to them.
- `about.md` is this guide.

Everything was made and checked with Blender 5.3.0, but only from the command line: I never opened Blender's window. The keys and menu paths below are ones Blender has used for many versions, and I believe they are right in 5.3; where I am less sure, the text says so.

## Opening the file

Start Blender from the app launcher, then use File > Open (Ctrl+O) and pick `orb.blend`. Or from a terminal in this folder:

```
blender orb.blend
```

You land in the Layout workspace (the tabs along the top of the window are workspaces, each a ready-made arrangement of editors). The big middle area is the 3D Viewport, looking through the scene's camera. On the right are the Outliner (top: a list of everything in the scene) and the Properties editor (below it: a column of small tab icons, each with a page of settings). Along the bottom is the Timeline.

The viewport probably starts in Solid mode: grey shapes, no colours. To see the real look, hover the mouse over the viewport, press Z and pick Rendered from the round menu that appears, or click the rightmost of the four small sphere buttons in the viewport's top-right corner. Rendered mode runs the renderer live, which may feel slow on this laptop's graphics chip, so switch back to Solid (Z, then Solid) when you want to move things around quickly. The build script asks for Rendered mode, but when I reopened the file without a window Blender reported Solid, so I could not confirm which you will see first.

A warning about dots in the viewport: the dot pattern is laid out on the pixels of the picture being drawn (see "Where the dots are made"). In the viewport that picture is the viewport itself, so the dots there may be a different size from the real render and may shimmer when you resize the window or zoom. The rendered image (F12) is the true result.

## What you are looking at

Click a name in the Outliner to select that thing; its settings then show in the Properties editor, and pressing N over the viewport opens a sidebar whose Item tab shows its Location, Rotation and Scale. The scene holds five objects:

- **Camera**: what the picture is taken from. It is orthographic, meaning no perspective: things do not shrink with distance, like a technical drawing. That makes it easy to line the scene up with the flat still. It is 38.4 Blender units wide, so one unit is exactly 100 pixels of the 3840-pixel picture. Numpad 0 looks through it at any time; on a laptop without a number pad, use View > Cameras > Active Camera in the viewport's menu bar.
- **Orb**: the egg. It is a plain UV sphere (a ball built from rings and segments) that has been stretched with its Scale, tilted with its Rotation, and made fatter at one end by a modifier called **Egg Shape** (a Simple Deform modifier set to Taper). Modifiers live in the Properties editor under the wrench tab. They change the shape without changing the stored mesh, so you can switch one off with its little monitor icon and back on again.
- **Backdrop**: a flat rectangle behind the orb in the Flexoki cream. It glows its own colour (an Emission material), so the light never shades it.
- **Sun**: the light. A Sun light shines in one direction as if from infinitely far away, so only its rotation matters, not where it sits. In the viewport it is a small circle with a line showing which way it shines.
- **Light Pivot**: an empty (an object with no shape, just a position and a rotation) at the orb's centre, drawn as a wire ball. The Sun is its child, so when the pivot turns, the Sun swings round the orb with it. This is how the animation works.

The axes: X runs left to right, Z runs up, and Y runs away from the camera. The camera stands at Y = -30 and looks along +Y.

There are two materials, shown in the Properties editor's Material tab (the red-and-white sphere icon) when the object is selected: **Cream Paper** on the Backdrop and **Orb Dots** on the Orb. The world, the empty space around everything, is called **Empty Sky**; it is black with strength 0, so it adds no light of its own.

The Timeline runs from frame 1 to frame 192: 8 seconds at 24 frames per second. With the mouse over the viewport, Space plays and stops, and Shift+Left Arrow jumps back to frame 1. Select the Light Pivot and the Timeline shows its two keyframes as small diamonds: at frame 1 its rotation is 0 degrees, and at frame 193 it is minus one full turn (-360 degrees) about Y. Frame 193 is never rendered, because it looks exactly like frame 1, and that is what makes the loop seamless. Between the two keys the rotation moves at an even speed (linear interpolation). The animation itself is stored in an action called **Light Goes Round**.

## Where the dots are made

All of the dot look is in the Orb's material. To see it, click the **Shading** workspace tab at the top of the window, then click the Orb in the Outliner. The lower half of the screen is now the Shader Editor, showing the nodes of **Orb Dots**. A node is a small box that takes values in on its left, does one thing, and passes the result out on its right; the lines carry values between them. If the nodes are off screen, hover over the editor and press Home. (The Shading workspace's viewport uses Material Preview, which lights the scene with a studio light instead of the Sun, so the orb there will not look like the render; press Z and pick Rendered to see the Sun's lighting.)

The nodes sit in three labelled frames:

1. **Light becomes darkness.** *Lit Surface* is an ordinary white Diffuse surface, lit by the Sun. *Shading As Colour* (a Shader to RGB node) turns that lighting into a plain number: 1 where the surface faces the sun, 0 where it faces away or is in shade. *Darkness* (a Map Range node) flips and stretches it into how much ink a spot should get: a spot facing away from the sun gets about 0.76, and the darkness falls to nothing before a spot faces the sun fully.
2. **Dot pattern on the screen.** *Screen Position* (a Texture Coordinate node, using its Window output) gives where this spot lands on the finished picture, from 0 to 1 across and from 0 to 1 up. *Dot Grid* (a Mapping node) scales that by 240 across and 135 up. *Bayer Thresholds* is a tiny 4 x 4 pixel image, repeated, that holds 16 different thresholds between 0 and 1. With the scaling, one repeat of it covers 16 x 16 rendered pixels, so each of its pixels covers a 4 x 4 square of the render: one dot. Its interpolation is set to Closest so each square stays one solid value. This arrangement of thresholds is called an ordered dither, or Bayer matrix, and it is the same one the still uses.
3. **Two colours.** *Ink Or Paper* (a Math node set to Greater Than) asks whether this spot's darkness is above the threshold of the square it falls in; the answer is 1 or 0. *Paper And Ink* (a Mix node) picks Flexoki black for 1 and Flexoki cream for 0, and *Flat Colour* (an Emission node) shows that colour exactly, with no further shading.

A darker spot beats more of the 16 thresholds, so more of the squares around it turn to ink. That is the whole trick.

A few settings elsewhere keep the result clean. In the Properties editor's Render tab (the camera-back icon), the render samples are 1, so every pixel is worked out once with no smoothing; and under Color Management there, the View Transform is Standard, so the cream and black come out as the exact Flexoki colours (Blender's default, AgX, is made for photographs and would shift them). In the Output tab (the printer icon), under Post Processing, Dither is 0, which stops Blender sprinkling faint noise over the saved image.

The render engine is EEVEE, Blender's fast engine that draws with the graphics chip. It works without a window on this machine and takes about a second per full-size frame. It is also the only engine where the Shader to RGB node works, which is what lets the material read its own lighting; Cycles, Blender's other engine, would ignore it.

## Experiments

Each of these changes one thing. Ctrl+Z undoes a change, and rebuilding (next section) undoes everything.

To render the current frame and look at it, press F12. A new window shows the picture after a few seconds; in it, Image > Save As (Shift+Alt+S) saves it. Close that window to get back.

### 1. Move the light

In the Layout workspace, click **Sun** in the Outliner. Move the mouse over the viewport, press R to rotate, move the mouse, and click to finish (right-click cancels). With the viewport in Rendered mode, the dots follow: the inky side of the orb is always the side facing away from the sun. For exact values, press N and type numbers into the Sun's Rotation fields in the sidebar's Item tab.

Try Rotation X = 90, Y = 0, Z = 0. That points the sun straight from the camera at the orb: the middle of the orb goes bare and only a dark rim stays.

### 2. Change the dot size

In the Shading workspace, with the Orb selected, click the **Dot Grid** node. Its Scale is X = 240, Y = 135: the number of 16-pixel pattern repeats across a 3840 x 2160 picture. Halve both (X = 120, Y = 67.5) and press F12: the dots are now 8 pixels wide. Double them (480 and 270) for 2-pixel dots. The node's Location Y of -0.125 shifts the grid down 2 pixels so it lines up exactly with the still; at other dot sizes it does not matter.

### 3. Change the orb's shape

Click **Orb** in the Outliner and press N. Its Scale is about X 3.14, Y 1.21, Z 2.80: half its width, depth and height, in units of 100 pixels. Set all three to 2.5 and render: a round, deeper ball, and because its surface now curves differently towards the light, the dots spread differently even where the outline barely changes. Then open the wrench tab in the Properties editor and change **Egg Shape**'s Factor: 0 is no taper, -0.335 is the egg from the still, and +0.5 moves the fat end to the other side.

### 4. Change how long the loop is

The length lives in two places that must agree: the scene's frame range and the frame of the pivot's second keyframe. To make a 4-second loop:

1. In the Properties editor's Output tab (the printer icon), set Frame End to 96.
2. Click **Light Pivot** in the Outliner. In the Timeline, click the keyframe diamond at frame 193 (it is past the end now, so scroll the Timeline with the mouse wheel or press Home over it to see all of it). With the mouse over the Timeline, press G, type -96 and press Enter. The key moves to frame 97.

Press Space: the light now goes round twice as fast. The rule is that the full turn sits on the frame just after Frame End. I could not try these clicks in the 5.3 window myself; if the Timeline does not let you move the key this way, the Dope Sheet editor does the same, and `build.py` does it for you with `LOOP_SECONDS = 4`.

### 5. Render a frame, or the whole loop

From this folder in a terminal:

```
./render.sh still      # renders/frame-0001.png, 3840x2160, a few seconds
./render.sh preview    # renders/loop-preview.mp4, 1280x720, about four minutes
```

Both run Blender without its window (`blender --background`). The preview renders every frame at full size and then scales the video down, because the dots are tied to pixels: rendering at 1280 x 720 directly would keep 4-pixel dots on a picture a third of the size, making them look three times bigger. Scaled down, the dots blend into soft grey, as they would on a 720p screen.

Inside Blender, F12 renders the current frame, and Ctrl+F12 renders the whole animation, frame by frame, to the folder named in the Output tab's Output panel (by default a folder in `/tmp`).

## Rebuilding the file

If you have broken something and want the original back, close Blender without saving and run this from this folder:

```
blender --background --python build.py
```

It makes `orb.blend` again from nothing in a few seconds, overwriting the old one, so copy the file first if you saved changes you want to keep. Every number worth changing (orb position and size, taper, light direction, darkness, dot size, colours, loop length) sits near the top of `build.py`; a lasting change is best made there and rebuilt.

Reading `build.py` from `main()` at the bottom shows the order a Blender scene is put together in: empty file, render settings, world, camera, backdrop, orb and its material, light, animation, save.

## How close the first frame is to the still

The scene's numbers (orb position, size, tilt, taper, light direction and the darkness range) were not guessed: I measured the still's dot pattern, worked out how dark each 16 x 16 pixel patch of it is, and fitted the 3D scene to that by computer, picking the values that made the rendered darkness closest. Then I rendered frame 1 at 3840 x 2160 and compared it with the still pixel for pixel.

What matches:

- The colours are exact: the render has only two colours in it, `#FFFCF0` and `#100F0F`, like the still.
- The dot grid is exact: same 4-pixel squares, same position on the screen, same ordered-dither pattern. Where both pictures have ink at a similar darkness, the very same squares are inked.
- Position: the centre of all the ink is at (1844, 921) in the render and (1846, 919) in the still, two pixels apart. The top edge is on the same row (702).
- Outline: the orb's area in the render overlaps the still's by 89% (the shared area divided by the area covered by either). The render's orb is about 11% smaller.
- Ink: 88% of the still's ink pixels are also ink in the render; counting ink in either picture, 82% is shared.
- Darkness spread, as the share of inked pixels in a 3 x 3 grid over the still's orb (still / render):

| | left | middle | right |
|---|---|---|---|
| top | 0.31 / 0.27 | 0.73 / 0.68 | 0.25 / 0.26 |
| middle | 0.53 / 0.57 | 0.59 / 0.52 | 0.22 / 0.22 |
| bottom | 0.20 / 0.19 | 0.20 / 0.18 | 0.03 / 0.03 |

Where it differs, which you can see by putting the two side by side:

- **The right edge.** In the still, the orb's right and lower-right side thins out into scattered dots, so its outline there is soft. The render's orb has a clean edge there. That is why the render's ink is 591 pixels wide against the still's 692, and 528 tall against 544.
- **The darkest part.** The still has one nearly solid patch of ink at the upper left that fades out in every direction. The render's dark side is a broad, even band along the top: a Diffuse surface in shade is simply "in shade", with no further gradient, and its darkness tops out at 0.76, so it is never solid ink. A real lit surface does not quite give the still's soft, wrapped-round gradient; the still was most likely drawn with a softer, made-up shading.
- **The outline follows the pixels, not the dots.** In the still, even the edge of the orb is made of whole 4 x 4 squares. In the render, the orb's edge cuts through squares, so along the edge you see part-squares. Blender decides for each pixel whether it is on the orb before the dot pattern is applied, so fixing this would need a different approach (doing the dots afterwards in the compositor).
- **Shape.** The fitted orb is quite flat front to back (half as deep as it is wide) and tilted 48 degrees; that combination gave the closest darkness, but it is a best fit, not a known truth about how the still was made.

In short, frame 1 is clearly the same picture in the same place with the same dots, but the lighting is a little harder and the right edge cleaner than the original.

## The loop

The animation turns the Light Pivot once round the camera's line of sight in 192 frames, so the light sweeps all the way round the orb and the inked side follows it: at frame 1 it comes from below (and a little to the right), at 2 seconds from the right, at 4 seconds from above, at 6 seconds from the left, and at 8 seconds it is back where it started. Because the light reaches the parts of the orb that are invisible in the still, the loop also shows the orb's whole egg-shaped outline as it goes.

I checked that the loop is seamless on full-size frames: from one frame to the next, between 1,575 and 1,825 pixels change; from frame 192 back to frame 1, 1,908 change, about the same as an ordinary step. In the small preview video the jump back to the start looks a little bigger in the numbers than other steps, because the video encoder stores the first frame differently from the rest, not because the scene jumps.
