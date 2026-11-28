# Solitude's climber, as a Blender base

A base for making an intro and a loop for Solitude's default background, `1-on-pole`: the climber in a hooded jacket, seen from behind, standing by a roped dome under a sky of stars and swirling cloud. The still is cut into five layers, each filled in where nearer layers hide it, and set up in Blender so that at rest it draws the still exactly. The file holds a ready Loop scene and a ready Intro scene, each pinned to the still where Omarchy needs it, and `render.sh` turns either into a video Omarchy takes.

The still is `solitude/1-on-pole.webp` in [omacom/omarchy-themes-backgrounds](https://github.com/omacom/omarchy-themes-backgrounds), 3160 x 2281. Omarchy ships an intro for it (4.6 s, 3160 x 2280, 3.8 MB) and no loop.

## What is here

| File | What it is |
|---|---|
| `parts.toml` | The judgment: the five layers, back to front, and where each one is |
| `masks/climber-ai.png` | The climber's cut-out from an AI background remover, as a 1-bit picture (7 KB) |
| `cut.py` | Finds the still by its SHA-256, cuts it into the layers, and fails unless they stack back into the still exactly |
| `build.py` | Run inside Blender: makes `out/base.blend`, one plane per layer, the Loop and Intro scenes, and with `-- render` renders it at rest |
| `render.sh` | Renders the Loop or the Intro of a base file and encodes it to Omarchy's rules |
| `check.py` | Compares a render with the still, pixel for pixel: the Base at rest, or any frame of the Loop or Intro |
| `out/` | Everything made: the layers, the filled-in picture, a contact sheet, `base.blend`. Not kept in git; rebuild it as below |

To rebuild everything, in this folder:

```
/usr/bin/python cut.py                        # out/parts/, out/clean.png, out/sheet.jpg
blender -b --python build.py -- render        # out/base.blend, out/rest.png
/usr/bin/python check.py                      # "No pixel differs"
```

The first two take seconds. Open the base with `blender out/base.blend`.

## Making a loop or an intro

The file has three scenes, picked from the scene menu at the top right of Blender's window:

| Scene | Size | Frames | Where the still must show |
|---|---|---|---|
| `Base` | 3160 x 2281 | 1 | Always: the reference the other two are copied from. Leave it still. |
| `Loop` | 3160 x 2280 | 1 to 240 (10 s) | Frame 1, and frame 241: the frame after the end, so frame 240 leads straight back into frame 1 |
| `Intro` | 3160 x 2280 | 1 to 144 (6 s) | Frame 144, the last, which hands the desktop back to the still |

The file opens on the Loop. Each scene has its own copy of the five layers (`loop sky`, `intro climber` and so on), sharing the pictures, so animating one scene never moves the other. Every layer already has a keyframe at rest on the frames in the table, shown by a marker named `still` on the Timeline. Animate between them: go to a frame, move, turn or scale a layer, press I over the viewport to key it. Don't move or delete the rest keys, and the loop's first frame and the intro's last frame stay the still.

Things to know while animating:

- **Units.** One Blender unit is 100 pixels: X is right, Y is up. The layers are stacked along Z, back to front, 1 unit apart, so a perspective camera could give parallax without reordering anything.
- **Pivots.** Every layer's origin is the centre of the picture, so scaling or turning a layer does so about the middle of the frame. To breathe the climber from his feet, or sway the dome from its base, parent the layer to an Empty placed there and animate the Empty, or put the 3D cursor there and use it as the pivot (the Pivot Point menu, top of the viewport).
- **The frame edge.** The layers are exactly the frame's size. Moving `sky`, `horizon` or `ground` sideways uncovers the edge, which renders magenta so it can't be missed. Scale those layers up a little (2% gives about 30 px of margin each side) for as long as they move, back to 1 on the rest keys.
- **The fills.** Behind the climber and the dome is the sky mirrored in from the left. Small motions hold up; larger ones show the mirror (see "Tried" below).
- **Lengths.** Omarchy asks for a loop of twenty seconds or less and an intro of five to seven. To change a length, change `TIMELINES` at the top of `build.py` and rebuild; that puts the rest keys and markers in the right place.
- **Keep the render settings.** Closest texture reads, filter 0.01, 1 sample, no dither, Standard view. Any other value and the rest frames stop being the still.

Save your work as a file of its own beside this guide (File > Save As, e.g. `loop-breath.blend`), not in `out/`: rebuilding replaces `out/base.blend`, and `out/` is not kept in git. Blender keeps the paths to the pictures relative, so the file works anywhere in this folder as long as `out/parts/` has been made.

Then, from this folder:

```
./render.sh loop  loop-breath.blend     # out/loop.mp4
./render.sh intro intro-rise.blend      # out/intro.mp4
/usr/bin/python check.py out/loop/frames/f-0001.png    # the loop's first frame is the still
/usr/bin/python check.py out/intro/frames/f-0144.png   # the intro's last frame is the still
```

`render.sh` renders every frame at full size (about 1.5 s a frame on this laptop, so a 10 s loop takes about 6 minutes) into `out/<loop|intro>/frames/`, then encodes H.264 High, level 5.1, 24 fps, bt709 colour tags. The loop gets exactly one keyframe and no B-frames, as the loops repository checks. It starts at CRF 16 (`CRF=20 ./render.sh loop ...` to change); before a pull request, find the highest CRF that still holds the VMAF numbers in `docs/fixed-ground.md`.

Inside Blender, F12 renders the current frame and Ctrl+F12 all frames, into `out/loop/` or `out/intro/`.

## The layers

| | Layer | What it holds | Cut by |
|---|---|---|---|
| 1 | `sky` | Stars and the swirling clouds, opaque, the whole picture | Everything |
| 2 | `horizon` | The bright band of cloud along the horizon | A band, y 1520 to 2040, edges fading over 80 px |
| 3 | `ground` | The snowy rocks along the bottom | A band from y 2030, edge fading over 40 px |
| 4 | `climber` | The climber, from his cap down to his legs under the dome | An AI cut-out, plus his cap, the shadowed left of his head and his left glove traced by hand, less the gaps of sky it took in, grown 3 px, edge fading over 3 px |
| 5 | `dome` | The roped dome at the front right, with its wires | An outline traced on full-size close-ups, raised over the wires, edge fading over 4 px |

The picture is pen hatching in two inks, so the cut that Kanagawa uses, snapping to areas of flat colour, would find thousands of specks here. The climber and the dome are cut by shapes instead.

- **The climber** comes from an AI background remover (Higgsfield's, run once on the still on 2026-11-28). It returned his outline at 2048 px wide; scaled up to the still, thresholded at half and cleaned to its one large piece, it is kept as `masks/climber-ai.png`, so rebuilding needs no service. It follows the jacket, harness and legs to a pixel or two, but gets two kinds of thing wrong, both fixed in `parts.toml`:
  - It took the dark cap, the shadowed left side of his head and most of the left glove for sky. Those are added (`add`) as polygons traced on 2x close-ups.
  - It took in gaps of sky as him: cloud between the left sleeve and the jacket, dark sky with stars between his left forearm and hip, cloud between the glove's fingers and its cuff, and dark sky between his right arm and the harness. Those are cut out again (`remove`). Its holes are deliberately not filled, since a filled hole is sky that would travel with him.
  
  The shape is then grown 3 px so the soft edge falls on sky. Anything of him left outside would stay painted on the sky and show as a ghost when he moves; anything of the sky left inside would travel with him.
- **Same ink, different thing.** The sky and his dark trousers, cap and harness are the same ink, #212A2E. No colour rule can tell them apart, only the drawing: ink lines and folds are him, cloud texture and stars are sky. A flat dark patch given to the wrong layer does not show at rest, only once it moves, so each such area was judged by eye at 2x. One, a patch beside his right thigh (about x 2610 to 2710, y 1420 to 1520), was first added to him and then judged sky.
- **Under the dome** the cut-out stops at the dome's edge, where his legs disappear. There the layer takes in an outline of just his two legs (`under` in `parts.toml`), painted flat trouser ink (`under.colour`), so moving the dome shows his legs going on behind it, not a copy of the dome's hatching or of the sky.
- **The dome** is an outline traced on full-size close-ups, a few pixels outside its edge. Between x 2650 and 2950 the wires along its top rise about 30 px above the dome itself; the outline goes over them so they move with it.

The first base, in the commit before this one, used outlines drawn by eye: the climber's took in large patches of sky down his left side and above his right shoulder, and the dome's left its top wires behind.

## What is behind

Where the climber and the dome hide the sky, horizon and ground, those layers are filled with the picture mirrored in along each row (`out/clean.png` shows the picture with both taken away): the left half of each hidden stretch from its left end, the right half from its right end. Mirroring keeps the hatching sharp and meets the edge without a step on both sides, which is the only place a small motion reveals; the one seam is in the middle, deep behind the climber. The first version mirrored from the left only, which left a hard seam down his right side that a 40 px move showed at once.

Because a layer's soft edge only ever falls over pixels where everything under it is still the original picture, the layers stack back into the still exactly. `cut.py` checks that on every run.

## The Blender scene

`out/base.blend` holds one plane per layer, named as above, 1 unit apart in depth, and an orthographic camera looking straight at them. One Blender unit is 100 pixels of the still, so moving a plane 0.05 along x moves it 5 pixels. Each plane's material shows its picture with no lighting: an image read pixel for pixel (Closest), its alpha mixing an Emission with a Transparent shader.

What makes the render the still, checked with `check.py`: the render is the still's own size, textures are read with Closest interpolation, the pixel filter is 0.01, dither is off, and the view transform is Standard with no look. Kanagawa found that Blender's defaults change 21.5% of pixels by more than 8 levels. With these settings no pixel differs here. Change them, and the first frame of a loop stops being the still.

## Tried: moving the layers apart

To see whether the fills hold, one frame was rendered with the climber 40 px right and 15 px up, the dome 20 px left, the sky 60 px left and the horizon 30 px right. That is far more than a loop would move. The climber leaves no hole, and the sky and horizon showing where he stood read as sky. Two things show:

- **The frame edge.** A full-picture layer moved sideways uncovers the edge of the frame (it renders grey). A loop has to scale the background layers up a little, or keep their motion inside a margin, or move only the climber and the dome.
- **The mirrored fill is plausible, not right.** Close up it repeats the sky on its left like a reflection. That is fine at the edge a small motion reveals, and not for a large one. A larger move would want the area painted, by hand or by an inpainting service as Kanagawa tried.

## What is rough or missing

- **No real motion yet.** The Loop and Intro scenes are ready but hold only rest keys. A 2-second test (the sky zooming 1.5% and the climber breathing 0.6%) went through `render.sh`: frame 1 and the frame before the end were the still to the pixel, the video had one I-frame and 47 P-frames, no B-frames, level 5.1 and bt709 tags.
- **The shipped intro cannot be made from this.** In it the climber climbs over the dome and straightens up: his pose changes, which flat layers cannot do. It is generated footage and stays a video. A loop is what this base is for: drifting cloud, a slow parallax, the climber breathing. A different, simpler intro could be made too.
- **The still is 2281 pixels tall, an odd number.** H.264 needs even sizes, so the Loop and Intro render 3160 x 2280, like the shipped intro: the still's last row is dropped. The players scale a video to the screen, so the row is not missed, but the video is not quite the still's shape.
- **The fill behind is still a mirror.** With the tighter cut there is much less of it, and it meets the picture without a step on both sides, which is all a small motion shows; moving the climber 40 px either way was checked and shows no edge and nothing of him left behind. A larger motion would show the reflection, most of all in the horizon band. Copying from one fixed distance to the left was tried instead: it kept the bands level but left hard seams where the copied sky was darker than its surroundings, so the mirror stayed. A proper fill wants painting, or an AI inpaint of the area behind the climber and the dome.
- **The climber's edge carries a thin rim.** Growing the shape 3 px and fading it over 3 more means a 3 to 5 px rim of whatever touches him moves with him: sky ink almost everywhere, which reads as his outline, but a few light flecks of cloud at the lower left of his head and around the left glove. At a small motion they are not seen; at a large one they would want a tighter hand-traced edge there.
- **The dark-on-dark edges are judgement calls**, as above: where trouser meets dark sky, the line follows the drawing as well as it can be read, not a colour.
- **The bands are straight cuts.** Moving the horizon against the sky slides one cloud texture over another along an 80 px fade. It has not been watched in motion.
