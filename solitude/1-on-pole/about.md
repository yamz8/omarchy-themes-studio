# Solitude's climber, as a Blender base

A base for making an intro and a loop for Solitude's default background, `1-on-pole`: the climber in a hooded jacket, seen from behind, standing by a roped dome under a sky of stars and swirling cloud. The still is cut into five layers, each filled in where nearer layers hide it, and set up in Blender so that at rest it draws the still exactly. Nothing moves yet; animating it is the next step, and an intro and a loop are both made from this same file.

The still is `solitude/1-on-pole.webp` in [omacom/omarchy-themes-backgrounds](https://github.com/omacom/omarchy-themes-backgrounds), 3160 x 2281. Omarchy ships an intro for it (4.6 s, 3160 x 2280, 3.8 MB) and no loop.

## What is here

| File | What it is |
|---|---|
| `parts.toml` | The judgment: the five layers, back to front, and where each one is |
| `cut.py` | Finds the still by its SHA-256, cuts it into the layers, and fails unless they stack back into the still exactly |
| `build.py` | Run inside Blender: makes `out/base.blend`, one plane per layer, and with `-- render` renders it at rest |
| `check.py` | Compares that render with the still, pixel for pixel |
| `out/` | Everything made: the layers, the filled-in picture, a contact sheet, `base.blend`. Not kept in git; rebuild it as below |

To rebuild everything, in this folder:

```
/usr/bin/python cut.py                        # out/parts/, out/clean.png, out/sheet.jpg
blender -b --python build.py -- render        # out/base.blend, out/rest.png
/usr/bin/python check.py                      # "No pixel differs"
```

Each step takes seconds. Open the base with `blender out/base.blend`.

## The layers

| | Layer | What it holds | Cut by |
|---|---|---|---|
| 1 | `sky` | Stars and the swirling clouds, opaque, the whole picture | Everything |
| 2 | `horizon` | The bright band of cloud along the horizon | A band, y 1520 to 2040, edges fading over 80 px |
| 3 | `ground` | The snowy rocks along the bottom | A band from y 2030, edge fading over 40 px |
| 4 | `climber` | The climber, from his cap down to his legs under the dome | An outline drawn by eye, edge fading over 6 px |
| 5 | `dome` | The roped dome at the front right, with its wires | An outline drawn by eye, edge fading over 6 px |

The picture is pen hatching in two inks, so the cut that Kanagawa uses, snapping to areas of flat colour, would find thousands of specks here. The climber and the dome are cut by outlines instead. The outlines were drawn on gridded copies of the still, then laid back over it and widened wherever a strip of arm, leg or shoulder fell outside: anything left out gets mirrored into the sky behind and shows as a pale fleck. They are a little loose on purpose, so a few pixels of sky move with the climber.

## What is behind

Where the climber and the dome hide the sky, horizon and ground, those layers are filled with the picture mirrored in from the left along each row (`out/clean.png` shows the picture with both taken away). Mirroring keeps the hatching sharp and meets the edge without a step, which is the only place a small motion reveals. The same is done for the climber's legs under the dome.

Because a layer's soft edge only ever falls over pixels where everything under it is still the original picture, the layers stack back into the still exactly. `cut.py` checks that on every run.

## The Blender scene

`out/base.blend` holds one plane per layer, named as above, 1 unit apart in depth, and an orthographic camera looking straight at them. One Blender unit is 100 pixels of the still, so moving a plane 0.05 along x moves it 5 pixels. Each plane's material shows its picture with no lighting: an image read pixel for pixel (Closest), its alpha mixing an Emission with a Transparent shader.

What makes the render the still, checked with `check.py`: the render is the still's own size, textures are read with Closest interpolation, the pixel filter is 0.01, dither is off, and the view transform is Standard with no look. Kanagawa found that Blender's defaults change 21.5% of pixels by more than 8 levels. With these settings no pixel differs here. Change them, and the first frame of a loop stops being the still.

## Tried: moving the layers apart

To see whether the fills hold, one frame was rendered with the climber 40 px right and 15 px up, the dome 20 px left, the sky 60 px left and the horizon 30 px right. That is far more than a loop would move. The climber leaves no hole, and the sky and horizon showing where he stood read as sky. Two things show:

- **The frame edge.** A full-picture layer moved sideways uncovers the edge of the frame (it renders grey). A loop has to scale the background layers up a little, or keep their motion inside a margin, or move only the climber and the dome.
- **The mirrored fill is plausible, not right.** Close up it repeats the sky on its left like a reflection. That is fine at the edge a small motion reveals, and not for a large one. A larger move would want the area painted, by hand or by an inpainting service as Kanagawa tried.

## What is rough or missing

- **No animation yet.** The next step is an intro and a loop made from this file, in their own scenes or frame ranges, each starting or ending at rest.
- **The shipped intro cannot be made from this.** In it the climber climbs over the dome and straightens up: his pose changes, which flat layers cannot do. It is generated footage and stays a video. A loop is what this base is for: drifting cloud, a slow parallax, the climber breathing. A different, simpler intro could be made too.
- **The still is 2281 pixels tall, an odd number.** H.264 needs even sizes, and the shipped intro is 3160 x 2280. Frames rendered from here will need their last row cut when they are encoded, and the comparison with the still made on the first 2280 rows.
- **The outlines are by eye.** The fill has been checked for flecks where it shows; the outline has not been checked all the way round at full size.
- **The bands are straight cuts.** Moving the horizon against the sky slides one cloud texture over another along an 80 px fade. It has not been watched in motion.
