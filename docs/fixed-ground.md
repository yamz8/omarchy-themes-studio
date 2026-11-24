# Fixed ground

What the studio does not get to decide. These are the rules Omarchy, OWE and the two clip repositories already set for any theme video. Everything not on this page is open.

Read from the source on 2026-11-24:

| Source | Version |
| --- | --- |
| omacom/omarchy, `quattro` | 372e1dec90 |
| omacom/owe, `main` | 4b71e73 (0.2.18) |
| omacom/omarchy-themes-intros, `master` | 7f73346 |
| omacom/omarchy-themes-loops, `master` | 298fcbc |

When one of these moves, check this page against it again.

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

**Loop**, enforced by `bin/check` in the loops repository on every pull request:

- H.264, exactly one keyframe, no B-frames
- `color_space`, `color_transfer` and `color_primaries` tags all present
- twenty seconds or less
- no larger than its still in either dimension, and the still's shape
- a frame count in the header (not a fragmented mp4), with every frame readable
- exactly one matching still in the theme

**Intro:** `bin/check` in the intros repository only checks that exactly one matching still exists. Nothing enforces a format. The shipped intros are H.264 High.

**Encode size**, set by the re-encode of every clip on 2026-11-22 (omarchy-themes-loops#2, omarchy-themes-intros#5). It is a practice a reviewer will hold a clip to, not a check in CI:

- x264's slowest preset at the highest CRF that still holds, against the reference: VMAF at least 96 on average, at least 94 on the worst 1% of frames, at least 95 on the frame that hands over to the still, and no more banding as measured by CAMBI
- codec, picture size, frame rate, frame count, pixel format and colour tags stay as they were
- the reason: video does not compress on the Omarchy ISO, so every MiB ships as it is

**Hardware decode**, observed and not yet accepted upstream: an H.264 stream above level 5.1 decoded with damage on an older Intel laptop (omarchy-themes-intros#7, still open). Until that is settled, treat level 5.1 as the ceiling.

## How it ships

- **Built-in themes:** a pull request adding `<theme>/<stem>.mp4` to the intros or loops repository. A release tagged `vYYYY.MM.DD` is picked up by omacom/omarchy-pkgs, and the package installs the clip to `/usr/share/omarchy/themes/<theme>/backgrounds/intros/` or `loops/`.
- **A user's own theme:** the files sit in the theme's `backgrounds/intros/` and `backgrounds/loops/`. `omarchy-theme-set` copies a theme's directories when it applies it, including for a theme installed from a git repository, so the videos should come along. That path has not been tested end to end.

## What a stock machine has

From omarchy `install/omarchy-base.packages`:

- **There:** `ffmpeg` (with libx264 and libvmaf in the current Arch build), `imagemagick`, `grim`, `gpu-screen-recorder`, `jq`, and Python itself.
- **Not there:** NumPy, Blender, `uv`. Anything the studio needs beyond the base set has to be installed by it or asked for.
