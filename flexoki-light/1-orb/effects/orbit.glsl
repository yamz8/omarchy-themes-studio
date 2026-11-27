// The light travels once round the orb in each cycle, and the dots follow it.
//
// The still is a sphere shaded in square dots: each dot is a 4x4-pixel cell
// of the still on a fixed grid, dark or paper, chosen by a 4x4 ordered (Bayer)
// dither of how dark the sphere is there. Its shading is close to one light
// falling on a sphere, which this states as a formula. The light is turned
// round the line of sight, and the sphere is dithered again on the same grid
// with the same matrix, so the dots keep their size, grid and colours.
//
// The formula misses the still's own dots in a few cells. Each cell is held
// on the side of its threshold the still puts it, and that hold is let go as
// the shading there changes, so with no turn every cell is the still exactly,
// and so is the end of each cycle.

uniform float turns; // whole turns of the light in one cycle

const float TURN = 6.2831853;
// The still's own size. OWE's `pixel` is a pixel of the screen being drawn,
// not of the still, so the dot grid is measured against this instead.
const vec2 STILL = vec2(3840.0, 2160.0);
const vec2 CENTRE = vec2(1917.11, 1074.87); // the sphere's centre, in pixels of the still
const float RADIUS = 372.0;
const vec3 LIGHT = vec3(0.34253, 0.75447, -0.55987); // where the light falls from at rest
const vec3 PAPER = vec3(1.0, 0.98824, 0.94118);   // #FFFCF0
const vec3 INK = vec3(0.06275, 0.05882, 0.05882); // #100F0F, dense ink
// Open paper; where dots are dense it is drawn a little yellower (see cell()).

float rank(vec2 cell) {
  int col = int(mod(cell.x, 4.0));
  int row = int(mod(cell.y, 4.0));
  vec4 r;
  if (row == 0) r = vec4(1.0, 9.0, 3.0, 11.0);
  else if (row == 1) r = vec4(14.0, 6.0, 12.0, 4.0);
  else if (row == 2) r = vec4(2.0, 10.0, 0.0, 8.0);
  else r = vec4(13.0, 5.0, 15.0, 7.0);
  return r[col];
}

// How dark the sphere is where its surface faces n, lit from l.
float shade(vec3 n, vec3 l) {
  return pow(clamp(-0.13533 - 1.05375 * dot(n, l), 0.0, 1.0), 1.32879);
}

// A cell's colour now, and whether it has changed from the still.
// The still's paper turns a little yellow where dots are dense (blue 240 on
// open paper, 208 from about half dark on), a mark of how it was compressed
// that reads as an olive cast over the mid-tones; the clean colours follow it.
vec3 cell(vec2 at, vec3 light, float turned, out bool changed) {
  vec2 middle = vec2(4.0 * at.x + 2.0, 4.0 * at.y + 4.0);
  bool was = dot(still(middle / STILL).rgb, vec3(0.299, 0.587, 0.114)) < 0.5;
  vec2 d = (middle - CENTRE) / RADIUS;
  float r2 = dot(d, d);
  changed = false;
  if (r2 > 1.03) return was ? INK : PAPER; // past every dot of the still
  // Cells on and just past the edge take the shading of the edge.
  vec3 n = r2 < 1.0 ? vec3(d, sqrt(1.0 - r2)) : vec3(d * inversesqrt(r2), 0.0);
  float rest = shade(n, LIGHT);
  float now = shade(n, light);
  float t = (rank(at) + 0.5) / 16.0;
  float hold = (was ? max(rest, t + 0.03125) : min(rest, t - 0.03125)) - rest;
  // Let go as the shading here changes, and everywhere as the light turns, so
  // no dot the formula does not account for stays pinned in place.
  hold *= 1.0 - smoothstep(0.02, 0.15, abs(now - rest) + 0.25 * turned);
  bool dark = now + hold > t;
  changed = dark != was;
  float dense = clamp(now / 0.45, 0.0, 1.0);
  return dark ? INK + vec3(-0.047, 0.0, -0.004) * (1.0 - dense) : PAPER - vec3(0.0, 0.0, 0.1255) * dense;
}

// The share of a screen pixel at x (in pixels of the still) that comes from
// the still's pixels before the edge: each of them weighted by a triangle as
// wide as a screen pixel is in the still, as the still is scaled to the screen.
float before(float x, float edge, float h) {
  float near = 0.0;
  float all = 0.0;
  for (int k = -3; k <= 3; k++) {
    float centre = floor(x) + 0.5 + float(k);
    float w = max(0.0, 1.0 - abs(centre - x) / h);
    all += w;
    near += centre < edge ? w : 0.0;
  }
  return near / all;
}

vec4 effect(vec2 uv) {
  float angle = TURN * turns * phase;
  float c = cos(angle);
  float s = sin(angle);
  vec3 light = vec3(c * LIGHT.x - s * LIGHT.y, s * LIGHT.x + c * LIGHT.y, LIGHT.z);
  float turned = TURN * turns * min(phase, 1.0 - phase); // how far from rest, in radians

  // Away from rest everything is drawn clean, so no ghost of a dot that has
  // moved stays in the still's compression marks; near rest it is the still.
  float away = smoothstep(0.3, 2.0, min(phase, 1.0 - phase) * seconds);
  vec2 p = uv * STILL;
  float wide = pixel.x * STILL.x; // pixels of the still in one pixel of the screen

  // On a screen so small that one of its pixels spans several dots (a preview,
  // or a screen under half the still's width), the scaled still shows the
  // dots' tone more than the dots, so the tone of the shading is drawn there.
  float coarse = smoothstep(2.0, 4.0, wide);
  vec4 tone = vec4(PAPER, 1.0);
  if (coarse > 0.0) {
    vec2 d = (p - CENTRE) / RADIUS;
    float r2 = dot(d, d);
    float f = r2 < 1.0 ? shade(vec3(d, sqrt(1.0 - r2)), light) : 0.0;
    float dense = clamp(f / 0.45, 0.0, 1.0);
    vec3 ink = INK + vec3(-0.047, 0.0, -0.004) * (1.0 - dense);
    vec3 paper = PAPER - vec3(0.0, 0.0, 0.1255) * dense;
    tone = vec4(mix(paper, ink, f), 1.0);
    if (coarse >= 1.0) return mix(still(uv), tone, away);
  }

  // OWE draws the still scaled to the screen, each screen pixel a triangle-
  // weighted mean of the still's pixels round it, as wide as one screen pixel
  // is in the still. The cells are drawn the same way, so moving dots keep the
  // look the still has on this screen. A dot is 4 pixels of the still, so on
  // any screen at least half the still's width this touches at most four.
  float h = clamp(wide, 1.0, 2.0);
  vec2 a = vec2(floor(p.x / 4.0), floor((p.y - 2.0) / 4.0));
  vec2 middle = vec2(4.0 * a.x + 2.0, 4.0 * a.y + 4.0);
  vec2 b = a + vec2(p.x < middle.x ? -1.0 : 1.0, p.y < middle.y ? -1.0 : 1.0);
  vec2 edge = vec2(p.x < middle.x ? 4.0 * a.x : 4.0 * a.x + 4.0, p.y < middle.y ? 4.0 * a.y + 2.0 : 4.0 * a.y + 6.0);
  float wx = p.x < middle.x ? 1.0 - before(p.x, edge.x, h) : before(p.x, edge.x, h);
  float wy = p.y < middle.y ? 1.0 - before(p.y, edge.y, h) : before(p.y, edge.y, h);

  bool c00;
  bool c10 = false;
  bool c01 = false;
  bool c11 = false;
  vec3 k00 = cell(a, light, turned, c00);
  vec3 k10 = k00;
  vec3 k01 = k00;
  vec3 k11 = k00;
  bool useX = wx < 0.999;
  bool useY = wy < 0.999;
  if (useX) k10 = cell(vec2(b.x, a.y), light, turned, c10);
  if (useY) k01 = cell(vec2(a.x, b.y), light, turned, c01);
  if (useX && useY) k11 = cell(b, light, turned, c11);
  else if (useX) k11 = k10;
  else if (useY) k11 = k01;
  vec4 clean = mix(vec4(mix(mix(k11, k01, wx), mix(k10, k00, wx), wy), 1.0), tone, coarse);

  // A dot that has moved is drawn at once; the rest comes clean gradually.
  bool changed = c00 || c10 || c01 || c11;
  return mix(still(uv), clean, changed && coarse == 0.0 ? 1.0 : away);
}
