// The picture is a collage of flat shapes: two pink, two teal and two lavender
// ones that let each other show through, and a white one, with line art drawn
// on them (rings, stripes, dashes, thin lines). Each shape breathes: it grows
// and shrinks a little about the place where it meets the edge of the picture,
// each in its own time, and the line art on it goes with it.
//
// There is only the still to work from, so the shapes are read out of its
// colours. Seven flat colours are every way the pink, teal and lavender can
// lie over the ground and over each other; a colour between two of them is the
// soft edge of a shape; anything else is line art, and what lies under it is
// read from the clean colours next to it. The picture is then put together
// again with each shape where it has got to.
//
// What the reading gets slightly wrong is measured at rest and given back at
// the two ends of the cycle, so the cycle starts and ends on the still.

uniform float amount; // how much a shape grows and shrinks, as a share of its size

const float TURN = 6.2831853;

// Every colour the shapes make, as this file has them. Bit 1 is lavender, 2
// pink, 4 teal.
const vec3 GROUND = vec3(255.0, 231.0, 235.0) / 255.0;
const vec3 LAVENDER = vec3(209.0, 196.0, 219.0) / 255.0;
const vec3 PINK = vec3(230.0, 178.0, 188.0) / 255.0;
const vec3 TEAL = vec3(164.0, 198.0, 198.0) / 255.0;
const vec3 LAVENDER_PINK = vec3(209.0, 160.0, 181.0) / 255.0;
const vec3 LAVENDER_TEAL = vec3(143.0, 180.0, 192.0) / 255.0;
const vec3 PINK_TEAL = vec3(151.0, 171.0, 173.0) / 255.0;
const vec3 WHITE = vec3(252.0, 255.0, 254.0) / 255.0;
const vec3 DARK = vec3(93.0, 75.0, 75.0) / 255.0; // the dark dashes
const vec3 MADE[8] = vec3[8](GROUND, LAVENDER, PINK, LAVENDER_PINK, TEAL, LAVENDER_TEAL, PINK_TEAL, LAVENDER_TEAL);

// Where each shape is anchored: pink, pink, teal, teal, lavender, lavender, white.
const vec2 ANCHOR[7] = vec2[7](vec2(0.0, 0.36621), vec2(0.96400, 0.74851), vec2(0.50723, 0.0), vec2(0.11216, 0.89037),
                               vec2(0.10615, 0.03442), vec2(0.90898, 0.07983), vec2(0.39895, 0.44845));

// Ten of the dark dashes touch the rings in the top left corner and go with
// them. Each is the line from one of its ends to the other.
const vec4 RINGED[10] = vec4[10](
  vec4(0.16194, 0.10673, 0.14863, 0.08465), vec4(0.10147, 0.09993, 0.10724, 0.11083),
  vec4(0.12772, 0.12554, 0.14107, 0.15746), vec4(0.15496, 0.13439, 0.16866, 0.16518),
  vec4(0.11047, 0.13611, 0.11868, 0.15302), vec4(0.08165, 0.15760, 0.08491, 0.16517),
  vec4(0.10112, 0.15910, 0.11219, 0.18174), vec4(0.18188, 0.17679, 0.18928, 0.19122),
  vec4(0.09316, 0.18437, 0.10541, 0.20846), vec4(0.13587, 0.20476, 0.12863, 0.19444));

const float FLAT = 0.016;  // this close to one of the colours, a place is that colour
const float FITS = 0.055;  // this close to the edge between two of them, a place may be that edge
const float SOLID = 0.118; // line art this far from what is under it is solid
const float REACH = 0.012; // how far to look for what is under line art, as a share of the height

// A dark dash at q is one of the ten that go with the rings.
bool ringed(vec2 q) {
  vec2 wide = vec2(aspect, 1.0);
  for (int k = 0; k < 10; k++) {
    vec2 a = RINGED[k].xy * wide;
    vec2 ab = RINGED[k].zw * wide - a;
    vec2 p = q * wide - a;
    vec2 d = p - ab * clamp(dot(p, ab) / dot(ab, ab), 0.0, 1.0);
    if (dot(d, d) < 0.011 * 0.011) return true;
  }
  return false;
}

vec3 on(int bits) {
  return vec3(float(bits & 1), float((bits >> 1) & 1), float((bits >> 2) & 1));
}

// The white shape lives here; white anywhere else is a dash of line art.
bool white_place(vec2 q) {
  return q.x > 0.30 && q.x < 0.50 && q.y > 0.30 && q.y < 0.585;
}

// A flat colour is made of whole shapes: how much lavender, pink and teal lie
// there (x, y, z, each 0 or 1) and whether the white shape does (w). False if
// the colour is none of them.
bool flat_colour(vec3 c, bool white, out vec4 m) {
  float least = FLAT * FLAT;
  bool found = false;
  m = vec4(0.0);
  for (int a = 0; a < 8; a++) {
    vec3 d = c - MADE[a];
    float e = dot(d, d);
    if (e < least) {
      least = e;
      m = vec4(on(a), 0.0);
      found = true;
    }
  }
  if (white) {
    vec3 d = c - WHITE;
    if (dot(d, d) < least) {
      m = vec4(0.0, 0.0, 0.0, 1.0);
      found = true;
    }
  }
  return found;
}

// The soft edge of one shape is a colour between two flat ones that differ by
// that shape. Gives the nearest such edge, which shape it is the edge of (0 to
// 2, or 3 for the white one), and how far the colour is from it.
float edge(vec3 c, bool white, out vec4 m, out int whose) {
  float least = 10.0;
  m = vec4(0.0);
  whose = 0;
  for (int a = 0; a < 8; a++) {
    for (int f = 0; f < 3; f++) {
      int b = a | (1 << f);
      if (b == a) continue;
      vec3 ab = MADE[b] - MADE[a];
      float len = dot(ab, ab);
      if (len < 0.0001) continue;
      float u = clamp(dot(c - MADE[a], ab) / len, 0.0, 1.0);
      vec3 d = c - (MADE[a] + u * ab);
      float e = dot(d, d);
      if (e < least) {
        vec3 s = on(a);
        if (f == 0) s.x = u;
        else if (f == 1) s.y = u;
        else s.z = u;
        least = e;
        m = vec4(s, 0.0);
        whose = f;
      }
    }
    if (white) {
      vec3 ab = WHITE - MADE[a];
      float u = clamp(dot(c - MADE[a], ab) / dot(ab, ab), 0.0, 1.0);
      vec3 d = c - (MADE[a] + u * ab);
      float e = dot(d, d);
      if (e < least) {
        least = e;
        m = vec4(on(a), u);
        whose = 3;
      }
    }
  }
  return sqrt(least);
}

// The colour the shapes make where this much of each lies.
vec3 paint(vec4 m) {
  vec3 without = mix(mix(MADE[0], MADE[1], m.x), mix(MADE[2], MADE[3], m.x), m.y);
  vec3 with_teal = mix(mix(MADE[4], MADE[5], m.x), mix(MADE[6], MADE[7], m.x), m.y);
  return mix(mix(without, with_teal, m.z), WHITE, m.w);
}

// What the flat places round a place are made of: the make-up most of them
// share, the one among them nearest the colour c, and the least and most of
// each shape among them.
vec4 around(vec2 q, vec3 c, bool white, out vec4 nearest, out vec4 close, out vec4 least, out vec4 most, out float found) {
  float gap = 10.0;
  float near_by = 0.0;
  nearest = vec4(0.0);
  close = vec4(0.0);
  float seen[9] = float[9](0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  least = vec4(1.0);
  most = vec4(0.0);
  found = 0.0;
  // Close by, for a line no wider than a ring's, then further out, and
  // further still only if nothing round here is flat.
  for (int ring = 0; ring < 3; ring++) {
    float far = ring == 0 ? 0.4 * REACH : ring == 1 ? REACH : 2.0 * REACH;
    for (int k = 0; k < 6; k++) {
      float turn = TURN * (float(k) + 0.5 * float(ring)) / 6.0;
      vec2 at = q + far * vec2(cos(turn) / aspect, sin(turn));
      vec4 m;
      if (flat_colour(still(at).rgb, white, m)) {
        int which = m.w > 0.5 ? 8 : int(m.x + 2.0 * m.y + 4.0 * m.z + 0.5);
        seen[which] += 1.0;
        if (ring == 0) {
          close += m;
          near_by += 1.0;
        }
        vec3 d = c - (which == 8 ? WHITE : MADE[which]);
        if (dot(d, d) < gap) {
          gap = dot(d, d);
          nearest = m;
        }
        least = min(least, m);
        most = max(most, m);
        found += 1.0;
      }
    }
    if (ring == 1 && found > 2.5) break;
  }
  // What the closest places are on average, when there are enough of them.
  close = near_by > 1.5 ? close / near_by : vec4(-1.0);
  int usual = 0;
  for (int a = 1; a < 9; a++) {
    if (seen[a] > seen[usual]) usual = a;
  }
  return usual == 8 ? vec4(0.0, 0.0, 0.0, 1.0) : vec4(on(usual), 0.0);
}

// What is at a place in the still: the shapes there, and the line art drawn
// over them, as its own colour and how solid it is.
//
// A colour that is not flat is either the soft edge of a shape or line art,
// and the colour alone cannot tell: the rim of a pale stripe over lavender
// looks like lavender thinning out. An edge has the shape on one side of it
// and not on the other, so the flat places round it differ by that shape;
// round line art they are all the same.
//
// Line art rides on a shape, `rider`: the dark dashes on the first pink one
// (but for the ten that touch the rings, which go with the rings), the white dashes on the
// second teal one, and rings, stripes and lines on the first lavender one in
// the top left of the picture and on the second pink one everywhere else. A dash is told by which way its colour leans from what is
// under it, so its soft rim goes with it.
vec4 shapes(vec2 q, out vec4 art, out int rider) {
  vec3 c = still(q).rgb;
  bool white = white_place(q);
  vec4 m;
  art = vec4(0.0);
  rider = -1;
  if (flat_colour(c, white, m)) return m;
  vec4 nearest, close, least, most;
  float found;
  vec4 mean = around(q, c, white, nearest, close, least, most, found);
  int whose;
  // An edge of the white shape needs the white shape next to it.
  float off = edge(c, white && most.w > 0.5, m, whose);
  vec4 spread = most - least;
  float across = whose == 0 ? spread.x : whose == 1 ? spread.y : whose == 2 ? spread.z : spread.w;
  // Where two edges run into one colour the colour cannot say what else lies
  // there (every edge of the white shape ends in white): the flat places can.
  if (found > 0.5) m.xyz = min(m.xyz, most.xyz);
  if ((off < FITS && found < 0.5) || (off < 1.6 * FITS && across > 0.5)) return m;
  // The white shape has nothing drawn on it: its rim is always its own.
  if (white && most.w > 0.5) return vec4(mean.xyz, clamp(dot(c - paint(vec4(mean.xyz, 0.0)), WHITE - paint(vec4(mean.xyz, 0.0))) / dot(WHITE - GROUND, WHITE - GROUND), 0.0, 1.0));
  // The rim of line art is nearly the colour under it, and that tells which
  // of the colours round it is under it. Solid art hides what it is on: there
  // it is what most of the places round it are.
  // Where a shape's edge runs under the art, the places closest by give it,
  // softly, on from either side.
  if (distance(c, paint(nearest)) < SOLID) mean = nearest;
  if (close.x >= 0.0 && most != least) mean = close;
  vec3 under = paint(mean);
  float solid = clamp(distance(c, under) / SOLID, 0.0, 1.0);
  art = vec4(solid > 0.05 ? clamp((c - (1.0 - solid) * under) / solid, 0.0, 1.0) : c, solid);
  vec3 lean = normalize(c - under + 0.00001);
  if (q.x < 0.32 && q.y < 0.45 && dot(lean, normalize(DARK - under)) > 0.94) rider = ringed(q) ? 4 : 0;
  else if (q.x < 0.6 && q.y > 0.42 && !white && dot(lean, normalize(WHITE - under)) > 0.94) rider = 3;
  else rider = q.x < 0.52 && q.y < 0.40 ? 4 : 1;
  return mean;
}

// Whether the shape `i`, or line art that rides on it, can be at q at all.
// Most of the picture is out of most shapes' reach, and is not read for them.
bool reaches(int i, vec2 q) {
  if (i == 0) return q.x < 0.34 && q.y > 0.06 && q.y < 0.67;
  if (i == 1) return (q.x > 0.55 && q.y > 0.28) || q.y > 0.82;
  if (i == 2) return q.x > 0.33 && q.x < 0.69 && q.y < 0.30;
  if (i == 3) return q.x < 0.57 && q.y > 0.43;
  if (i == 4) return q.x < 0.53 && q.y < 0.40;
  if (i == 5) return q.x > 0.57 && q.y < 0.47;
  return white_place(q);
}

float ease(float a, float b, float v) {
  v = clamp((v - a) / (b - a), 0.0, 1.0);
  return v * v * (3.0 - 2.0 * v);
}

// Where in the still the shape `i` has brought to the place uv.
vec2 from(vec2 uv, int i, float planted) {
  float lag = 0.4 + 1.1 * float(i);
  float size = 1.0 + amount * (sin(TURN * phase + lag) - sin(lag));
  vec2 home = ANCHOR[i] + (uv - ANCHOR[i]) / size;
  return uv + (home - uv) * planted;
}

vec4 effect(vec2 uv) {
  // Nothing moves at the edges of the picture, so what runs off it stays put.
  float planted = ease(0.0, 0.06 / aspect, uv.x) * ease(0.0, 0.06 / aspect, 1.0 - uv.x) * ease(0.0, 0.06, uv.y) * ease(0.0, 0.06, 1.0 - uv.y);

  vec4 art;
  int rider;
  vec4 lies = vec4(0.0);
  vec4 dark = vec4(0.0), pale = vec4(0.0), top = vec4(0.0), rest_of = vec4(0.0);
  for (int i = 0; i < 7; i++) {
    vec2 q = from(uv, i, planted);
    if (!reaches(i, q)) continue;
    vec4 m = shapes(q, art, rider);
    if (i == 0) lies.y = max(lies.y, m.y * step(q.x, 0.45));
    else if (i == 1) {
      lies.y = max(lies.y, m.y * step(0.45, q.x));
      // The teal rings and lines in the lower right are drawn on this shape.
      lies.z = max(lies.z, m.z * step(0.38, q.y) * step(0.45, q.x));
    }
    else if (i == 2) lies.z = max(lies.z, m.z * step(q.y, 0.38));
    else if (i == 3) lies.z = max(lies.z, m.z * step(0.38, q.y) * step(q.x, 0.45));
    else if (i == 4) lies.x = max(lies.x, m.x * step(q.x, 0.40));
    else if (i == 5) lies.x = max(lies.x, m.x * step(0.40, q.x));
    else lies.w = m.w;
    if (art.a > 0.0 && rider == i) {
      if (i == 0) dark = art;
      else if (i == 3) pale = art;
      else if (i == 4) top = art;
      else if (i == 1) rest_of = art;
    }
  }
  vec3 now = paint(lies);
  // Rings, stripes and lines first; the dashes lie over them.
  now = mix(now, top.rgb, top.a);
  now = mix(now, rest_of.rgb, rest_of.a);
  now = mix(now, dark.rgb, dark.a);
  now = mix(now, pale.rgb, pale.a);

  // The same reading with nothing moved, against the still itself: only
  // near the two ends of the cycle, where it is given back.
  float ends = 1.0 - ease(0.0, 0.12, phase) * ease(0.0, 0.12, 1.0 - phase);
  if (ends <= 0.0) return vec4(now, 1.0);
  vec4 m = shapes(uv, art, rider);
  vec3 read = mix(paint(m), art.rgb, art.a);
  return vec4(now + (still(uv).rgb - read) * ends, 1.0);
}
