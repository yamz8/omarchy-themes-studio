// The five stripes sway. Each slides sideways, row by row, on a wave that
// travels down the picture: the middle one stays, the pair next to it moves
// one way and the other, and the outer pair moves further. Where the stripes
// fan out the outer pair also widens and narrows.
//
// The picture is five lanes, one for each stripe, with dark ground between
// them. Each lane is looked up where its stripe has come from, so a stripe
// moves whole and its edges stay as sharp as they are in the still.
//
// How far each stripe moves at each height was measured from the loop this
// scene stands in for, by measure.py, which writes the tables below: values
// at seventeen heights from the top of the picture to the bottom, as shares of
// its width. Each is a sine part and a cosine part of one wave of the cycle,
// and the cosine part is taken from where it stands at the start, so at the
// start, and each time the cycle comes round, the picture is the still.

uniform float amount; // 1 is the motion as measured

// TABLES

const float TURN = 6.2831853;

// A table's value at a height, between its two nearest entries.
float at(float table[17], float y) {
  float place = clamp(y, 0.0, 1.0) * 16.0;
  int below = int(min(floor(place), 15.0));
  return mix(table[below], table[below + 1], place - float(below));
}

// How far apart the stripes' middles are at a height: the same down the
// straight part, then fanning out.
float apart(float y) {
  float u = max(y - FAN_FROM, 0.0);
  return APART + FAN_SQUARE * u * u + FAN_LINE * u;
}

vec4 effect(vec2 uv) {
  float wave = sin(TURN * phase);
  float back = cos(TURN * phase) - 1.0;
  float gap = apart(uv.y);
  float lane = floor((uv.x - 0.5) / gap + 0.5);
  // Ground, unless a stripe has come to this place: the still beyond the
  // lanes, and between two lanes what is at the middle of the dark between.
  vec4 colour = abs(lane) > 2.5 ? still(uv) : still(vec2(0.5 + (lane + 0.5) * gap, uv.y));
  // The stripes move a few thousandths of the width, so only the lane a
  // place is in and the ones beside it can reach it.
  for (int beside = -1; beside <= 1; beside++) {
    float k = lane + float(beside);
    if (abs(k) > 2.5) continue;
    float outer = step(1.5, abs(k));
    float moved = sign(k) * amount * mix(at(INNER_SIN, uv.y) * wave + at(INNER_COS, uv.y) * back,
                                         at(OUTER_SIN, uv.y) * wave + at(OUTER_COS, uv.y) * back, outer);
    float wider = outer * amount * (at(WIDER_SIN, uv.y) * wave + at(WIDER_COS, uv.y) * back);
    float middle = 0.5 + k * gap;
    // Where in the still this place of the moved, widened stripe came from.
    float home = middle + (uv.x - middle - moved) / (1.0 + wider / (0.75 * gap));
    if (abs(home - middle) > 0.5 * gap) continue;
    vec4 found = still(vec2(home, uv.y));
    // A stripe is lighter than the ground, so the lighter is the stripe.
    if (dot(found.rgb, vec3(1.0)) > dot(colour.rgb, vec3(1.0))) colour = found;
  }
  return colour;
}
