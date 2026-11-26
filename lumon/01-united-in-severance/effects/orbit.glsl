// A light runs once round the globe's outline in each cycle, clockwise, with
// a tail fading behind it. It comes up over a third of a second, goes round,
// and fades out just before the cycle ends. It takes the outline's own stroke
// towards white and leaves a faint glow just off it.
//
// The oval comes from the still; the light's speed, where it starts and how
// its tail fades were measured from the loop this scene stands in for, by
// measure.py. Distances here are shares of the still's height.

uniform vec2 middle; // the middle of the oval, in the still
uniform vec2 radii;  // half its width and half its height, to the middle of its stroke, as shares of the still's height
uniform vec2 run;    // seconds into the cycle its head would be at the right end, and rounds a second
uniform float glow;  // how strong the light is just off the stroke, against 1 on it

// How far round the oval each of sixteen equal turns of its angle is, from
// the right end, clockwise, as shares of the whole way round: the oval is
// wider than it is tall, so equal angles are not equal distances.
const float ROUND[17] = float[17](0.0000, 0.0435, 0.0999, 0.1706, 0.2500, 0.3294, 0.4001, 0.4565, 0.5000,
                                  0.5435, 0.5999, 0.6706, 0.7500, 0.8294, 0.9001, 0.9565, 1.0000);

const float TURN = 6.2831853;
const float WAY = 0.7682;     // the whole way round, as a share of the height
const float THIN = 0.00116;   // half the stroke's thickness at the oval's ends
const float THICK = 0.00185;  // and at its top and bottom
const float SOFT = 0.00046;
const float SPREAD = 0.0030;
const float RISE = 0.028;     // the head brightens over this far
const float HOLD = 0.093;     // and stays full this far behind it
const float FADE = 0.171;     // then fades to a third in this far
const float FULL = 0.97;

vec4 effect(vec2 uv) {
  vec4 here = still(uv);
  float now = phase * seconds;
  // Up at the start of its round and out at the end.
  float up = smoothstep(0.36, 0.72, now) * (1.0 - smoothstep(9.25, 9.70, now));
  if (up <= 0.0) return here;
  vec2 from = vec2((uv.x - middle.x) * aspect, uv.y - middle.y);
  vec2 unit = from / radii;
  float out_by = length(unit);
  if (out_by < 0.5) return here;
  // How far from the middle of the stroke, about.
  float off = abs(out_by - 1.0) * out_by / length(unit / radii);
  if (off > SPREAD * 7.0) return here;
  float angle = atan(unit.y, unit.x);
  if (angle < 0.0) angle += TURN;
  float place = angle / TURN * 16.0;
  int below = int(min(floor(place), 15.0));
  float along = mix(ROUND[below], ROUND[below + 1], place - float(below));
  // How far this place is behind the light's head, the way it runs.
  float behind = fract((now - run.x) * run.y - along) * WAY;
  float strong = FULL * smoothstep(0.0, RISE, behind) * exp(-max(behind - HOLD, 0.0) / FADE)
               * (1.0 - smoothstep(0.75 * WAY, 0.95 * WAY, behind));
  float half_stroke = mix(THIN, THICK, unit.y * unit.y / (out_by * out_by));
  float beside = glow * exp(-max(off - half_stroke, 0.0) / SPREAD);
  float lit = up * strong * mix(1.0, beside, smoothstep(-SOFT, SOFT, off - half_stroke));
  return vec4(here.rgb + (1.0 - here.rgb) * lit, 1.0);
}
