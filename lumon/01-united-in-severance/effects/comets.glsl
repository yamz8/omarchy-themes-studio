// A light runs along each of the five lines, left to right, one after
// another: a bright head with a tail fading behind it, each tail its own
// length. A light takes the line's own stroke towards white and leaves a
// faint glow just off it, so the drawing never changes shape.
//
// Where the lines are comes from the still; how fast a light runs, when each
// sets off, and how long its tail is were measured from the loop this scene
// stands in for, by measure.py. Every light is off the picture when the cycle
// starts, so at the start, and each time it comes round, the picture is the
// still.

uniform float speed; // how far a light runs in a second, as a share of the still's width
uniform float glow;  // how strong the light is just off the stroke, against 1 on it

// The middle of each line, as a share of the still's height.
const float LINE[5] = float[5](0.56019, 0.57963, 0.59954, 0.61944, 0.63889);
// When each light's head is at the left edge, in seconds into the cycle.
const float ENTER[5] = float[5](1.58, 1.09, 0.07, 2.08, 0.58);
// How quickly each tail fades and where it ends, as shares of the still's width.
// The two longest are ended a little short of what was measured, so that they
// are off the picture when the cycle comes round.
const float FADE[5] = float[5](0.066, 0.085, 0.203, 0.061, 0.141);
const float TAIL[5] = float[5](0.248, 0.280, 0.520, 0.219, 0.450);

const float HALF = 0.00139;   // half a line's thickness, as a share of the height
const float SOFT = 0.00046;   // the stroke's soft edge
const float SPREAD = 0.0030;  // how far the glow reaches before it has faded to a third
const float LEAD = 0.0081;    // the light begins this far ahead of where the head is counted from, as a share of the width
const float RISE = 0.020;     // it brightens over this far
const float HOLD = 0.060;     // and stays full to this far
const float FULL = 0.86;      // how far towards white a light takes the stroke

vec4 effect(vec2 uv) {
  vec4 here = still(uv);
  float now = phase * seconds;
  float lit = 0.0;
  for (int i = 0; i < 5; i++) {
    float off = abs(uv.y - LINE[i]) - HALF;
    if (off > SPREAD * 6.0) continue;
    // How far this place is behind the light's head.
    float behind = mod(now - ENTER[i], seconds) * speed - uv.x + LEAD;
    if (behind < 0.0 || behind > TAIL[i]) continue;
    float strong = FULL * smoothstep(0.0, RISE, behind) * exp(-max(behind - HOLD, 0.0) / FADE[i])
                 * (1.0 - smoothstep(0.8 * TAIL[i], TAIL[i], behind));
    float beside = glow * exp(-max(off, 0.0) / SPREAD);
    lit = max(lit, strong * mix(1.0, beside, smoothstep(-SOFT, SOFT, off)));
  }
  return vec4(here.rgb + (1.0 - here.rgb) * lit, 1.0);
}
