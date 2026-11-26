# Hackerman, synth scape

A wave of light crosses the wireframe mountains, from the far ridge towards the viewer, once every 3.8 seconds. Nothing is cut out of the still. The scene is one effect of its own, `effects/pass.glsl`, working on the band of the picture the mountains are in, with a grey picture, `pieces/light.webp`, that says where the light falls and how much. It has no arrive part, so the theme's intro clip still plays.

| | Shipped loop | Scene |
|---|---|---|
| Size | 3,692,696 bytes | 72,273 bytes (the light map 69,188, the shader 1,970, the scene file 1,115) |

What it costs to run has not been measured: it was only drawn to files.

## How it was made

The shipped loop is the still plus a change lifted from a source video, so there is no formula to copy. `cut.py` measures the loop instead, and finds that the whole of it is three things:

- **Where the light falls, and how much.** Each place gets its own amount: most on the lines, less in a glow round them, none on the floor or the sky. This is the grey picture.
- **When.** Each place lights up once. The moment the light is at its height there runs from frame 17 at the far ridge to frame 80 at the near slopes, and a polynomial of the place (fourth degree, 15 numbers) gives it to within half a frame. It is written into the shader.
- **How.** In every place the light comes up and goes down as the same bell, 5.2 frames wide. The cycle comes round, so the end of one pass runs into the start of the next.

The light's colour was measured too: a white with a little less red in it, which adds less to a colour the fuller that colour already is. That is why the cyan lines gain mostly red and turn white, while the blue faces between them gain all three.

`cut.py` writes the picture and the shader, and sets the two numbers in `scene.jsonc` that go with them.

## How close it is

`check.py` draws all 92 frames with the real player at 1920x1360 and compares them with the loop, each measured from its own first frame:

- Where the loop is lit (10% of the picture) it changes 3.96 levels on average. The scene is 1.42 levels from it on average and 2.36 on its worst frame, and the two changes agree 0.927, where 1 is the same change.
- The light peaks on the same frame as the loop's, or one frame off, in every band from far to near.
- At its height the light is 96% to 100% of the loop's in every band.
- From its last frame to its first the scene does not step. The loop steps 0.32 levels.

On six busy frames, inside the band, the changes agree 0.937 at 3840x2720, 0.955 at 2400x1700 and 0.962 at 1280x906. Side by side the frames look the same; what differs is fine colour noise along the edges of the lines.

## What differs from the loop

- **The loop's light is not exactly one bell per place.** Its source was a video, and each line's light has its own small irregularities. The scene gives every place the same bell. This is most of the 1.4 levels.
- **A faint afterglow.** After the pass, the loop leaves about a third of a level of extra light on the far mountains until its last second. The scene has none.
- **The loop's grain.** Away from the mountains the loop changes 0.3 levels, from video compression. The scene changes nothing there.
- **The loop's first frame** is a little darker than the still all over, from its colour conversion. The scene at rest is the still.
- **The light map is 1920 pixels wide.** On a 4K screen the glow round the lines is a little softer than the loop's.

The shader is valid as both GLSL 1.50 and GLSL ES 3.00, checked with glslangValidator wrapped as the player wraps it. It has only been run under desktop OpenGL.
