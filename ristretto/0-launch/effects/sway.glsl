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

const float INNER_SIN[17] = float[17](-0.00048, -0.00007, 0.00062, 0.00133, 0.00188, 0.00228, 0.00244, 0.00237, 0.00209, 0.00161, 0.00098, 0.00029, -0.00044, -0.00112, -0.00172, -0.00228, -0.00264);
const float INNER_COS[17] = float[17](-0.00228, -0.00230, -0.00222, -0.00195, -0.00145, -0.00082, -0.00010, 0.00063, 0.00128, 0.00172, 0.00198, 0.00215, 0.00207, 0.00179, 0.00131, 0.00075, 0.00035);
const float OUTER_SIN[17] = float[17](-0.00088, -0.00008, 0.00122, 0.00250, 0.00360, 0.00442, 0.00488, 0.00500, 0.00468, 0.00393, 0.00281, 0.00152, -0.00020, -0.00250, -0.00509, -0.00750, -0.00907);
const float OUTER_COS[17] = float[17](-0.00484, -0.00488, -0.00473, -0.00423, -0.00339, -0.00227, -0.00097, 0.00040, 0.00171, 0.00282, 0.00371, 0.00458, 0.00530, 0.00537, 0.00439, 0.00266, 0.00160);
const float WIDER_SIN[17] = float[17](0.00031, 0.00027, 0.00021, 0.00017, 0.00008, 0.00001, -0.00003, -0.00007, 0.00001, 0.00024, 0.00049, 0.00029, -0.00081, -0.00303, -0.00505, -0.00457, -0.00147);
const float WIDER_COS[17] = float[17](0.00032, 0.00037, 0.00043, 0.00046, 0.00047, 0.00045, 0.00040, 0.00034, 0.00027, 0.00016, 0.00050, 0.00154, 0.00259, 0.00291, 0.00145, -0.00024, 0.00041);

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
  float u = max(y - 0.5781, 0.0);
  return 0.0417 + 0.8222 * u * u + 0.0468 * u;
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
