// A swell passes over the picture from left to right, once a cycle. Each dot
// grows as it passes and shrinks back. A dot is grown by looking around each
// place for a lit one within reach: every dot keeps its own middle and its
// round edge, wherever it sits, and nothing has to know where the dots are.
//
// Small dots grow much further than large ones, so the shader has to know
// which kind a place is beside. The area's shape tells it: white in the room
// round a small dot, mid grey in the room round a large one. The player also
// mixes this effect into the still by that shape, which would leave a large
// dot's growth half drawn, so what is returned for a place is taken that much
// further from the still, and the mix lands where it should.
//
// How far a dot has grown at each moment of the swell's passing was measured
// from the loop this scene stands in for, by cut.py, which writes the two
// tables below: one value a frame at 24 a second, from a second before the
// swell's middle to a second after, as shares of the reach.

uniform vec2 reach; // how much is added to a dot's radius at the swell's height, small dots then large, as shares of the still's height
uniform vec2 sweep; // the swell is at a place sweep.x + sweep.y * x seconds into the cycle, x from 0 to 1 across

// TABLES

const float TURN = 6.2831853;

// How far the swell has grown a dot of each kind, moments from its middle, 0 to 1.
vec2 grown(float moments) {
  float place = clamp(moments * 24.0 + 24.0, 0.0, 48.0);
  int below = int(min(floor(place), 47.0));
  float part = place - float(below);
  return vec2(mix(SMALL[below], SMALL[below + 1], part), mix(LARGE[below], LARGE[below + 1], part));
}

vec4 effect(vec2 uv) {
  vec4 here = still(uv);
  float room = mask(uv);
  if (room <= 0.0) return here;
  // Seconds from the swell's middle at this place, the short way round the cycle.
  float moments = mod(phase * seconds - sweep.x - sweep.y * uv.x + 0.5 * seconds, seconds) - 0.5 * seconds;
  vec2 each = reach * grown(moments);
  float within = room > 0.75 ? each.x : each.y;
  if (within <= 0.0) return here;
  // The lightest of what lies within reach, round about and halfway.
  float light = here.r;
  for (int spoke = 0; spoke < 16; spoke++) {
    float angle = TURN * float(spoke) / 16.0;
    vec2 way = vec2(cos(angle) / aspect, sin(angle)) * within;
    light = max(light, still(uv + way).r);
    if (spoke % 2 == 0) light = max(light, still(uv + way * 0.5).r);
  }
  vec3 wanted = max(here.rgb, vec3(light));
  return vec4(here.rgb + (wanted - here.rgb) / room, 1.0);
}
