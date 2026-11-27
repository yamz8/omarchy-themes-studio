# Omarchy themes studio

Where moving backgrounds for Omarchy themes get worked out: the intro that plays when a background appears, and the loop that keeps it moving afterwards. Every theme Omarchy ships has a folder here, whether or not anything has been made for it yet.

The finished videos for the built-in themes live in [omacom/omarchy-themes-intros](https://github.com/omacom/omarchy-themes-intros) and [omacom/omarchy-themes-loops](https://github.com/omacom/omarchy-themes-loops), and the stills in [omacom/omarchy-themes-backgrounds](https://github.com/omacom/omarchy-themes-backgrounds). None of those files are copied here. The studio holds the working material beside them: descriptions, the few pictures a description needs, the scripts that make and check them, and notes on what was learned.

## The idea being tried

A video stores every frame. A **scene** stores a description instead: a small text file beside the still that says which parts of it move and how, with a shader or a few cut pictures where the description needs them. OWE, Omarchy's wallpaper engine, draws the still and the moving parts live, so nothing is decoded and what ships is kilobytes.

- A scene's idle part plays where a theme loop would, and its arrive part where an intro would.
- With nothing moving a scene is its still, to the pixel, so it can stop and start anywhere.
- A scene cannot stand in for generated footage such as smoke, a camera move or a face. Those stay videos.

The player is proposed to OWE in [omacom/owe#56](https://github.com/omacom/owe/pull/56), a draft, and the format is described there in `docs/scenes.md`. The small Omarchy change that lets a scene play as an intro is [omacom/omarchy#20350](https://github.com/omacom/omarchy/pull/20350), also a draft.

## Every theme

What Omarchy ships for each theme, and what the studio has. A **scene** follows the shipped video and is cheaper to run; a **study** was built to learn something and is not a candidate as it stands; a **draft** is unfinished. Each theme's page lists its backgrounds one by one.

<!-- themes: written by bin/themes -->
| Theme | Backgrounds | Intros | Loops | In the studio |
|---|---|---|---|---|
| [catppuccin](catppuccin/README.md) | 4 | 3 | 1 | [1-totoro](catppuccin/1-totoro/): scene |
| [catppuccin-latte](catppuccin-latte/README.md) | 2 | 1 | 1 | [1-color-fade](catppuccin-latte/1-color-fade/): scene |
| [ethereal](ethereal/README.md) | 4 | 1 |  |  |
| [everforest](everforest/README.md) | 2 | 1 |  |  |
| [flexoki-light](flexoki-light/README.md) | 2 | 1 |  | [1-orb](flexoki-light/1-orb/): study |
| [gruvbox](gruvbox/README.md) | 6 | 1 |  |  |
| [hackerman](hackerman/README.md) | 3 | 1 | 1 | [1-synth-scape](hackerman/1-synth-scape/): scene |
| [jade-horse](jade-horse/README.md) | 4 | 1 |  |  |
| [kanagawa](kanagawa/README.md) | 2 | 1 |  | [1-kanagawa](kanagawa/1-kanagawa/): study |
| [last-horizon](last-horizon/README.md) | 4 | 1 |  |  |
| [lumon](lumon/README.md) | 3 | 2 | 1 | [01-united-in-severance](lumon/01-united-in-severance/): scene |
| [lupine](lupine/README.md) | 6 | 1 |  |  |
| [matte-black](matte-black/README.md) | 4 | 1 |  |  |
| [miasma](miasma/README.md) | 3 | 1 |  |  |
| [nord](nord/README.md) | 4 | 1 |  | [0-black-moon](nord/0-black-moon/): draft |
| [retro-82](retro-82/README.md) | 9 | 1 |  |  |
| [ristretto](ristretto/README.md) | 5 | 1 | 1 | [0-launch](ristretto/0-launch/): study |
| [rose-pine](rose-pine/README.md) | 4 | 1 | 1 | [1-funky-shapes](rose-pine/1-funky-shapes/): study |
| [solitude](solitude/README.md) | 5 | 1 |  |  |
| [starship](starship/README.md) | 4 | 1 |  |  |
| [tokyo-night](tokyo-night/README.md) | 9 | 1 |  |  |
| [vantablack](vantablack/README.md) | 5 | 1 | 1 | [0-dot-hands](vantablack/0-dot-hands/): scene |
| [white](white/README.md) | 4 | 1 | 1 | [1-white](white/1-white/): scene |
<!-- /themes -->

## What a background's folder holds

A background that has been worked on has a folder named after its still, such as `catppuccin/1-totoro/`:

| File | What it is |
|---|---|
| `about.md` | What was made, how close it is to the shipped video in numbers, and what is still rough. Start here. |
| `scene.jsonc` | The scene: the description OWE plays. |
| `pieces/`, `effects/` | The pictures and shaders the scene names. Many scenes have no pictures at all. |
| `cut.py`, `measure.py` | The script that made those pictures, or measured the motion from the shipped video. |
| `check.py` | Draws every frame of the scene with the real player and compares it with the shipped video. Run as `./check.py <path to owe-render>`. |

Two folders hold something else: `kanagawa/1-kanagawa/` is an early try at cutting a still into parts and inks, and `flexoki-light/1-orb/` has the same picture made as a Blender file and as a vector file, to compare those routes with a scene.

## Working here

- `bin/themes` rewrites the table above and each theme's page from what Omarchy has installed and from `notes.toml`. Run it after Omarchy's backgrounds change or after editing `notes.toml`.
- A still is never copied, converted or renamed. Scripts find it in the installed packages by name and check it by its SHA-256, so a scene can only be made for the exact picture it will play over.
- The checks need `owe-render` built from the OWE branch above, and Python with NumPy, SciPy and Pillow. On Omarchy that is `/usr/bin/python`.
- [`docs/fixed-ground.md`](docs/fixed-ground.md) sets out what Omarchy fixes for any moving background: where it goes, when it plays, its format and how it ships.

## What has been learned so far

- All eight shipped loops have a scene that follows the video. Six are cheaper to run than their video, White only by a little; Rose Pine costs as much as its video and Ristretto more. The heavy ones point at two gaps in the format: an effect cannot read a picture of data, and pieces cannot overlap or change size.
- Where a picture was made by a rule, stating that rule in a small shader gives the smallest and closest result: 2 KB for Catppuccin Latte against a 4 MB loop.
- Together the eight scenes are about 0.35 MB against 24 MB of loops. Most of the shipped intros are generated footage and stay as they are.
- Apart from side-by-side demos of Totoro and Latte, nothing here has been watched playing by a person. The numbers say how close each scene is; whether it looks right is still open.
