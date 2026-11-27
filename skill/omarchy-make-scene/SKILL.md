---
name: omarchy-make-scene
description: >
  Make an Omarchy background move with a scene: a small text file beside a still that says which parts of the picture move and how, which OWE (Omarchy's wallpaper engine) draws live in place of a loop video or an intro video. Covers choosing the kind of motion that fits a picture, writing scene.jsonc, its shape pictures and shaders, looking at it and checking it with the tools here, estimating its cost, and putting it where it plays. Use when asked to make a background move, animate a wallpaper, make a live background, a loop or an intro for a still, or to change how an existing scene moves. Picking, adding or switching backgrounds belongs to the omarchy skill, and making a theme to omarchy-make-theme. Triggers: make this background move, animate the wallpaper, live background, moving wallpaper, scene, scene.jsonc, loop for a background, intro for a background, twinkling stars, drifting water
---

# Making a Scene for an Omarchy Background

A scene moves a still without a video. It is one text file, `scene.jsonc`, in a folder beside the still, sometimes with a shader or a few shape pictures next to it. OWE draws the still and the moving parts over it, so what ships is kilobytes and nothing is decoded. A scene's `idle` part repeats for as long as the desktop may move (animations on, AC power), where a loop video would play. An optional `arrive` part plays once when the background appears, where an intro video would.

**The one rule: with nothing moving, a scene is its still, to the pixel.** OWE stops and starts a scene at any moment by fading it into the still, so everything a scene does has to start from the still and come back to it. A scene never draws a picture of its own; it moves and redraws what the still already shows.

`format.md` beside this file is the full format. `examples/color-fade/` is a complete small scene. The tools are in `tools/` beside this file; below, `$SKILL` is this folder.

## 0. Check that this OWE can draw scenes

```bash
owe scene info "$SKILL/examples/color-fade/scene.jsonc"
```

JSON starting `{"status":` means it can. A usage message means this OWE has no scenes yet (they are proposed in https://github.com/omacom/owe/pull/56). Then nothing below can run: tell the user and stop. Do not try to imitate a scene with a video.

## 1. Look at the still and decide what kind of motion fits

Open the still and look at it (`readlink -f ~/.local/state/omarchy/current/background` is the one on screen). Ask what in it would move in real life, and how that could be said. Pick the first row that fits:

| The picture has | Use | Cost and effort |
|---|---|---|
| Stars, lights, water, mist, clouds, a glow: something that shimmers or drifts in place | One of OWE's own effects (`twinkle`, `glow`, `drift`, `flow`) on an area | A few lines. Start here whenever it fits. |
| A look that was made by a rule: bands, waves, stripes, dots, a gradient, anything you could describe as a formula | A shader of the scene's own that states the rule and moves it | One short shader. The smallest and closest results come this way. |
| Separate flat things on a plain ground that should each move: a character, a moon, small shapes | Cut pieces | The most work: each piece needs its shape and what is behind it. Only on flat artwork. |
| Motion that needs imagery the still does not hold: smoke, a camera move, a turning head, things appearing from nowhere | Not a scene | Say so and stop. That is footage, and it stays a video. |

Keep it small. One or two things moving quietly reads better on a desktop than everything moving, and each effect costs drawing time.

## 2. Start the scene

```bash
"$SKILL/tools/scene-start" /path/to/still.webp --into ~/scenes/<name>
```

With no still it takes the background on screen. It prints the still's name and SHA-256 and writes `scene.jsonc` with both in it and every part empty and explained. Work in that folder. **Never copy, convert, resize or rename the still**: the scene holds the checksum of the exact file, and OWE refuses it for any other.

## 3. Write the motion

Places are shares of the picture, 0 to 1: `"at": [left, top, width, height]`. Distances and sizes are shares of the still's height, so a scene looks the same on every screen. Never write pixels.

**An effect of OWE's on an area.** Name the area, then list the effect under it in `idle`:

```jsonc
"areas": [ { "name": "sky", "mask": "pieces/sky.png", "at": [0, 0, 1, 0.6] } ],
"idle": { "frames_a_second": 12, "sky": { "twinkle": { "amount": 0.5, "size": 0.003, "seconds": 8 } } }
```

What each value does. Distances are shares of the still's height, so 0.003 is about 3 pixels on a 1080-high screen. `seconds` is one cycle of the effect.

| Effect | Value | What it does | Calm | Strong |
|---|---|---|---|---|
| `twinkle` | `amount` | How far a point's brightness swings, as a share of how much it stands out from what is round it. Near 1 a star can fade out completely. | 0.3 to 0.5 | 0.8 to 1 |
| | `size` | The widest point of light that twinkles. Anything brighter than its surroundings and narrower than this is taken for a point; larger stars with halos are left alone. | 0.002 to 0.004 | up to 0.006 |
| | `seconds` | | 7 to 10 | 4 to 6 |
| `glow` | `amount` | How much brighter and dimmer the whole area gets, as a share of its brightness. | 0.05 to 0.1 | 0.2 to 0.3 |
| | `flicker` | 0 breathes slowly and evenly; 1 is restless like a flame. | 0 | 0.5 to 1 |
| | `seconds` | | 5 to 8 | 3 to 5 |
| `drift` | `amount` | Two numbers: how far the picture is pushed across and down by slow swells. | `[0.003, 0.001]` | `[0.01, 0.004]` |
| | `size` | How wide one swell is. Small makes a ripple, large a slow heave. | 0.05 to 0.15 | |
| | `seconds` | | 9 to 16 | 5 to 8 |
| `flow` | `amount` | Two numbers: how far the picture travels across and down in one cycle. It is two copies taking turns, so on fine detail keep it small or the copies show. | `[0.01, 0]` | `[0.04, 0]` |
| | `seconds` | | 10 to 16 | 5 to 8 |

The twinkle and drift ranges come from scenes that use them; glow and flow have not been used in a finished scene yet, so treat theirs as a place to start. Left out, a value takes OWE's own: twinkle 0.6 and 0.004 over 6 s, glow 0.12 and 0 over 5 s, drift `[0.004, 0.002]` and 0.08 over 12 s, flow `[0.02, 0]` over 10 s. `drift` and `flow` move less where the area's mask is darker, so a mask that fades towards what should hold still (a shore, a horizon) keeps edges from tearing.

An area with no `mask` is its whole rectangle. A mask is a grey picture of the area's shape, white where the effect works in full and black where the still is left alone. Make it from the still itself, small and soft, and look at it after making it.

**`twinkle` finds thin bright edges as well as points.** The lit rim of a cloud, a ridge line, snow on a mountain or a thin streak is brighter than what is beside it too, so with no mask it sparkles along with the stars. A mask made by brightness cannot help: stars and rims are both bright. Make the mask from structure instead, which leaves open sky white and blacks out wherever there is an edge:

```python
from PIL import Image, ImageFilter
left, top, wide, tall = 0.0, 0.0, 1.0, 1.0           # the area's "at"
still = Image.open(STILL).convert("L")
w, h = still.size
box = still.crop((round(left * w), round(top * h), round((left + wide) * w), round((top + tall) * h)))
box = box.resize((1024, round(1024 * box.height / box.width)))   # a shape is soft and needs few pixels
plain = box.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))    # the points of light are gone; what has edges is left
rims = plain.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(4))  # how strong an edge is nearby
rims.point(lambda v: 0 if v > 4 else 255).filter(ImageFilter.GaussianBlur(3)).save("pieces/sky.png")
```

On a nebula with cloud ridges this kept almost nine in ten of the stars twinkling and took the sparkle off nineteen in twenty rim pixels. The `4` is the line between sky and rim: lower it to black out more, raise it to keep more sky. For other effects a mask is usually a region (the water, the sky above a skyline); cut it the same way and replace the last three lines with whatever separates that region, then look at it.

**A shader of the scene's own.** Declare it under `effects`, give it an area, and write one function. `examples/color-fade/effects/waves.glsl` is the model: it shifts where the still is read by a wave, measured against where the wave stands at the start of the cycle, so the cycle begins and ends on the still.

```glsl
uniform float amount;            // a value the scene sets; one uniform per value
vec4 effect(vec2 uv) {           // the colour at this place of the still, now
  float push = sin(6.2831853 * (uv.x - phase)) - sin(6.2831853 * uv.x);
  return still(uv + vec2(0.0, push * amount));
}
```

It is given `still(uv)`, `mask(uv)`, `phase` (0 to 1 over the effect's `seconds`, then again), `seconds`, `pixel`, `aspect`, `area`, `grain(p)` and `cloud(p)`; `format.md` says what each is.

**Cut pieces.** Each piece needs a `picture` (its shape: grey, white where it is solid), a `behind` patch (what the still would show there once the piece moves away, as colour, see-through outside the shape) and its place. A part then moves its `x`, `y`, `size` or `fade` with `swing`, `pulse` or `from`. This only works where what is behind a piece can be known, which means a flat or evenly shaded ground. Before trying, read how a working scene cuts its pieces: `cut.py` in https://github.com/yamz8/omarchy-themes-studio/tree/main/catppuccin/1-totoro.

## 4. Look at it

```bash
owe scene info scene.jsonc                              # does OWE accept it, and why not
owe scene frame scene.jsonc --at 3 --out moment.png     # one moment, 3 seconds into the idle part, 1920x1080 unless --size WxH
"$SKILL/tools/scene-sheet" scene.jsonc --out sheet.png --zoom zoom.png
"$SKILL/tools/scene-sheet" scene.jsonc --part arrive --out arrive.png
```

Open the pictures and look at them yourself. `owe scene frame` uses the code that draws a playing scene, so what it writes is what plays. If OWE cannot find the still from where the scene is, add `--still /path/to/still` to each command (`scene-start` says when).

- `sheet.png` is eight moments evenly through one cycle. It shows large motion: a piece moving, a band rising, a light passing.
- **Motion a few pixels wide cannot be seen on the sheet, or on a whole frame.** Stars, sparkles, thin lines and small dots look identical in every moment. `zoom.png` is for that: on top, the whole still with everything that changes marked in red, the marks drawn large; below, the three busiest places at twice full size, each at rest, when most changed, and with its changes marked. Read it and ask of every red mark: is this on something I meant to move? Scattered marks on stars are a twinkle. A row of marks along an edge, a rim or a horizon is the effect catching the edge, and needs a mask (step 3). `--places "0.3,0.6 0.7,0.2"` enlarges places you name, as shares of the picture across and down.
- A video cannot be watched from here. `--video preview.mp4` writes one for the user, and `--beside reference.mp4` puts a video to follow on its left. To judge calm without watching, read the `pace` line of the check below.

## 5. Check it

```bash
"$SKILL/tools/scene-check" scene.jsonc --map where.png
```

It must pass before anyone is shown the scene, and takes about a minute. It checks that at rest the scene is its still, that something visibly changes and where, that each thing the idle part lists changes something in its own place and nothing changes elsewhere, and that nothing jumps where a cycle ends and starts again. Its `pace` line says how far a pixel steps from one frame to the next: small steps are calm, and one that jumps a large part of its range between two frames may flicker. It warns when two effects share an area.

**Passing is not the same as right.** The check cannot tell a star from a bright edge, or say whether the motion looks good; a scene that sparkles in the wrong places passes every line. `where.png` and step 4's `zoom.png` are where that shows. Do not go on until you have read them.

## 6. Estimate what it costs

```bash
"$SKILL/tools/scene-cost" scene.jsonc --wide 2560       # the user's screen in pixels across
```

A scene only earns its place if it is cheaper to draw than a video. This times OWE drawing frames to files against drawing the still alone, several times over. It is rough: it cannot see less than about 10 ms a frame, and on a busy machine its tries can disagree by more than that.

- `--wide` is the screen's width in pixels: `hyprctl monitors -j | jq -r '.[] | "\(.width)x\(.height) scale \(.scale)"'`. With a scale that is not a whole number OWE may draw larger (1920 wide at scale 1.6 was drawn 2400 wide on one laptop), so when unsure test the next size up too.
- It gives a verdict only when its tries agree. **"No verdict" means run it again**, with more `--tries` or when the machine is quieter. Do not change the scene because of one noisy run.
- "Heavy" as a verdict is real: lower `frames_a_second` (12 is enough for slow motion such as twinkling and drifting; 24 is for something quick), make the area smaller, or find what the shader works out again for every pixel.

The measurement that counts is the scene playing on the desktop.

## 7. Show the user, and put it where it plays

Show the sheet and the zoom picture and say plainly what moves, what you could not do, and what the cost estimate said. To play it, the scene's folder goes beside the still the desktop is showing, named after the still, and OWE is told to look again:

```bash
home=~/.local/state/omarchy/current/theme/backgrounds/scenes
mkdir -p "$home" && cp -r ~/scenes/<name> "$home/<still's name without its ending>"
owe refresh
```

It plays while animations are on and the machine is on AC power. That folder is rebuilt each time a theme is applied, so to keep the scene also put it in `~/.config/omarchy/themes/<theme>/backgrounds/scenes/<name>/`; `scene-start` prints both paths.

## Traps that cost time

- **A shader must compile as both GLSL 1.50 and GLSL ES 3.00.** Write every number with a decimal point (`2.0`, not `2`), give loops fixed bounds, and avoid names the language reserves in either version: `patch`, `sample`, `filter`, `input`, `output`, `common`, `partition` and `active` are reserved in GLSL ES and easy to reach for. A scene's values cannot be named `phase`, `seconds`, `pixel`, `aspect`, `area`, `strength`, `still`, `mask`, `grain`, `cloud` or `effect`. A shader that does not compile refuses the whole scene; `owe scene frame` prints the compiler's line.
- **A cycle must come round.** Use `phase` only inside something that repeats, such as `sin` or `cos` of a whole number of turns, or measure against where things stood at the start of the cycle as the example does. `still(uv + phase * something)` slides and then jumps back; `scene-check` reports that as a failed seam.
- **An effect fades in.** OWE brings every effect up from the still over the first 0.4 seconds of the idle part. A moment drawn at `--at 0` is always the still; look at `--at 1` or later to see the effect.
- **`twinkle` catches bright edges**, not only stars: cloud rims, ridge lines, snow, thin streaks. See the mask in step 3, and read `zoom.png` before believing it is only the stars.
- **Effects do not add up.** Each effect reads the still, not what an earlier effect drew. Two effects listed on one area: only the last shows, and the check passes anyway (it prints a warning). Two areas that overlap: where both shapes are white, the later one wins. Give each effect its own area with a shape that does not overlap the others, or write one shader that does both things.
- **A shader is run for every pixel of its area, every frame.** A long formula, a table looked up in a loop, or many reads of the still (more than about ten) can cost more than playing a video. A scene made this way for striped artwork cost more than its video; one for seven overlapping shapes cost as much. If the estimate says heavy, the scene is not done.
- **Reading the still between pixels softens hard edges.** A shader that shifts sharp line art by a fraction of a pixel blurs it slightly. Fine for soft pictures; for hard edges keep shifts small or expect softness.
- **Comparing with a video.** When a scene is made to follow an existing video, decode the video with `ffmpeg -vf scale=flags=accurate_rnd+full_chroma_int,format=rgb24`. The default conversion comes out about a level dark and looks like a difference that is not there.
- **A piece that is listed is drawn, one that is not is part of the still.** A part moves only the pieces it lists. No two pieces may share a pixel of the still.

## What a scene cannot do today

Say so to the user when the picture needs one of these; do not work around it with a heavy shader.

- Pieces cannot overlap, show through each other, or carry a colour that mixes with what is under them.
- A piece's `size` and `fade` cannot swing back and forth; only `x` and `y` take `swing` and `pulse`. Pieces cannot turn.
- An effect can read only the still and its area's shape. It cannot be handed a picture of data of its own.
- At most 8 areas, 32 pieces, 8 effects, and 8 values an effect.
- Scenes do not play on the lock screen, which shows the still.
- Nothing stops a scene that is too heavy for the machine; that is why step 6 is not optional.

## Examples to read

`examples/color-fade/` here is a whole scene in two files. More, each with an `about.md` saying how it was made and how close it came, are in https://github.com/yamz8/omarchy-themes-studio:

| For | Read |
|---|---|
| OWE's own effects on masked areas | `nord/0-black-moon` |
| A shader that moves the whole picture by a formula | `catppuccin-latte/1-color-fade`, `white/1-white` |
| A shader with one picture of where light falls | `hackerman/1-synth-scape` |
| Several small shaders on separate places | `lumon/01-united-in-severance` |
| Cut pieces, with an arrive part | `catppuccin/1-totoro` |
| What too heavy looks like, and why | `rose-pine/1-funky-shapes`, `ristretto/0-launch` |
