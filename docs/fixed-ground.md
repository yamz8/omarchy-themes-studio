# Fixed ground

What the studio does not get to decide. These are the rules Omarchy, OWE and the three theme repositories already set for any theme video. Everything not on this page is open.

Read from the source on 2026-11-24, and again on 2026-11-26 after the stills moved to a repository of their own:

| Source | Version |
| --- | --- |
| omacom/omarchy, `quattro` | 0f240028ba |
| omacom/owe, `main` | 4b71e73 (0.2.18) |
| omacom/omarchy-themes-backgrounds, `master` | 3590a3e |
| omacom/omarchy-themes-intros, `master` | fd582b3 |
| omacom/omarchy-themes-loops, `master` | 4c158ea |

When one of these moves, check this page against it again.

## Where a still lives

- **Built-in themes:** in omacom/omarchy-themes-backgrounds as `<theme>/<name>`, since 2026-11-25. The omarchy repository holds no stills any more. The `omarchy-themes-backgrounds` package installs them to `/usr/share/omarchy/themes/<theme>/backgrounds/<name>`, so that is where every Omarchy machine has them, a dev-linked one too.
- **One name joins everything:** the intro and the loop in their own repositories belong to the still with the same `<theme>/<stem>`.
- **A user's theme:** `~/.config/omarchy/themes/<theme>/backgrounds/`, and extra backgrounds for any theme in `~/.config/omarchy/backgrounds/<theme>/`.
- **Applying a theme** (`omarchy-theme-set`) copies the packaged `backgrounds/`, with its `intros/` and `loops/`, into the theme it stages, without overwriting a file the theme ships itself.
- **A theme with no backgrounds at all** gets one drawn when it is applied: `backgrounds/omarchy.png`, the Omarchy mark in the theme's accent on its background colour, 3840x2160 (`omarchy-theme-bg-generate`).
- **A still can change on its own.** A pull request to the backgrounds repository can replace, rename or remove one without touching its videos. The clip repositories check for that only by name.

## Where a video goes

A video belongs to one still and is found by name, with no registration.

- **Intro:** `intros/<stem>.<ext>` beside the still `<stem>.<image ext>`. Video extensions are tried in this order: `mp4`, `m4v`, `mov`, `webm`, `mkv`, `avi`. (`resolve_intro` in omarchy `bin/omarchy-theme-bg-boot-intro`)
- **Loop:** `loops/<stem>.mp4` beside the still. Only `mp4`. (`owe_theme_loop_for` in owe `src/common/xdg.c`)
- **Stills** that can have a video: `jpg`, `jpeg`, `png`, `bmp`, `webp`.
- The lookup is relative to the still's own directory, so it works the same for a built-in theme, a user theme in `~/.config/omarchy/themes/<theme>/backgrounds/`, and extra backgrounds in `~/.config/omarchy/backgrounds/<theme>/`.
- A video placed directly in `backgrounds/` is something else: an ordinary video wallpaper. It shows in the background picker, gets no intro, and is not held to the loop rules.

## When it plays

**Intro** (omarchy `docs/theming.md`, owe `README.md`)

- Plays at login, when switching to a theme with that background selected, and when that background is chosen within the current theme.
- Does not play on a shell restart, a theme refresh, or a headless setup, and not while animations or the intro toggle are off.
- Muted, and cut off at 30 seconds.
- Starts on its own first frame, under a 420 ms crossfade the shell provides, so a fade from black is unnecessary.
- Ends by handing the desktop back to the still, so its last frame has to be the still.
- Asked for: five to seven seconds, opening on the scene's setup.

**Loop** (omarchy `docs/theming.md`, owe `README.md`)

- Plays in the still's place while Hyprland's animations are on and the machine is on AC power, after the still's intro if it has one.
- Gives way to the still on battery and when animations are turned off.
- The background link keeps naming the still, so the picker, theme memory and the lock screen never see the loop.
- Its first frame is the still, and its last frame leads straight back into the first.
- Asked for: small, steady motion through the whole clip, with no easing in or out at the ends, and twenty seconds or less.

## Format

**Loop**, enforced by `bin/check <omarchy-themes-backgrounds checkout>` in the loops repository, on every pull request and once a week (a still renamed or removed leaves its loop behind without a push there):

- H.264, exactly one keyframe, no B-frames
- `color_space`, `color_transfer` and `color_primaries` tags all present
- twenty seconds or less
- no larger than its still in either dimension, and the still's shape
- a frame count in the header (not a fragmented mp4), with every frame readable
- exactly one matching still in the theme

**Intro:** `bin/check <omarchy-themes-backgrounds checkout>` in the intros repository only checks that exactly one matching still exists. Nothing enforces a format. The shipped intros are H.264 High.

**Encode size**, set by the re-encode of every clip on 2026-11-22 (omarchy-themes-loops#2, omarchy-themes-intros#5). It is a practice a reviewer will hold a clip to, not a check in CI:

- x264's slowest preset at the highest CRF that still holds, against the reference: VMAF at least 96 on average, at least 94 on the worst 1% of frames, at least 95 on the frame that hands over to the still, and no more banding as measured by CAMBI
- codec, picture size, frame rate, frame count, pixel format and colour tags stay as they were
- the reason: video does not compress on the Omarchy ISO, so every MiB ships as it is

**Hardware decode:** an H.264 stream above level 5.1 decoded with damage on an older Intel laptop. The Hackerman intro was re-encoded at level 5.1 for it (omarchy-themes-intros#7, merged); the same change for nine more intros is open (omarchy-themes-intros#9). No check enforces it. Treat level 5.1 as the ceiling.

## How it ships

- **Built-in themes:** a pull request adding `<theme>/<stem>.mp4` to the intros or loops repository, for a still already in the backgrounds repository. A release tagged `vYYYY.MM.DD` is picked up by omacom/omarchy-pkgs, and the package installs the clip to `/usr/share/omarchy/themes/<theme>/backgrounds/intros/` or `loops/`. Stills, intros and loops are three packages released on their own dates.
- **A user's own theme:** the files sit in the theme's `backgrounds/intros/` and `backgrounds/loops/`. `omarchy-theme-set` copies a theme's directories when it applies it, including for a theme installed from a git repository, so the videos should come along. That path has not been tested end to end.

## What a stock machine has

From omarchy `install/omarchy-base.packages`:

- **There:** `ffmpeg` (with libx264 and libvmaf in the current Arch build), `imagemagick`, `grim`, `gpu-screen-recorder`, `jq`, and Python itself.
- **Not there:** NumPy, Blender, `uv`. Anything the studio needs beyond the base set has to be installed by it or asked for.
