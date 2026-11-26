// A slow wave travels outward through the folds of the paper, from the grey
// opening, and moves each fold across its own edge. A fold moves by the same
// amount along its whole length, so its edge stays smooth.
//
// FOLD is where the folds are: a number for every place that grows steadily
// across the folds, outward, as a share of the still's height. It is written
// as a formula, a sum of 45 smooth shapes, which folds.py worked out from
// the still; do not edit the numbers by hand.
//
// A fold's shift is measured against where the wave stands at the start of
// the cycle, so at the start, and each time it comes round, the picture is
// the still exactly. The wave keeps the same speed all the way round.

uniform float amount; // how far a fold moves at most, as a share of the still's height
uniform float wave;   // the length of one wave across the folds, as a share of the still's height

const float TURN = 6.2831853;
// The grey opening: its middle and its radii, as shares of the still. Inside it nothing moves.
const vec2 OPENING_AT = vec2(0.0637, 0.5597);
const vec2 OPENING_SIZE = vec2(0.2766, 0.3843);
const int DEGREE = 8;
const float FOLD[45] = float[45](
  0.9052118, -0.0546075, 0.0836898, 0.0083184, -0.0099961,
  -0.0029020, 0.0015562, 0.0005827, -0.0000360, 0.6755965,
  0.0336848, -0.0833915, -0.0118017, 0.0151817, 0.0044626,
  -0.0023696, -0.0011237, 0.0321486, -0.0020488, 0.0224832,
  0.0047332, -0.0068403, -0.0025420, 0.0015279, -0.0336365,
  -0.0017054, 0.0048936, -0.0001446, 0.0018023, 0.0004216,
  0.0097263, -0.0001512, -0.0080425, -0.0013783, 0.0010816,
  -0.0006658, 0.0000613, 0.0029980, 0.0007083, -0.0000919,
  0.0006135, 0.0018863, -0.0001384, -0.0002563, -0.0001186);

// The still at a place between its pixels, read through a sharper curve than the plain blend of the
// four nearest: with that blend a fold's hard edge goes soft whenever it sits between pixels, and
// the paper would lose its crispness as soon as it moved. Nine blended reads make sixteen pixels.
vec4 crisp(vec2 uv) {
  vec2 place = uv / pixel;
  vec2 whole = floor(place - 0.5) + 0.5;
  vec2 f = place - whole;
  vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f));
  vec2 w1 = 1.0 + f * f * (-2.5 + 1.5 * f);
  vec2 w2 = f * (0.5 + f * (2.0 - 1.5 * f));
  vec2 w3 = f * f * (-0.5 + 0.5 * f);
  vec2 mid = w1 + w2;
  vec2 a = (whole - 1.0) * pixel;
  vec2 b = (whole + w2 / mid) * pixel;
  vec2 c = (whole + 2.0) * pixel;
  return (still(vec2(a.x, a.y)) * w0.x + still(vec2(b.x, a.y)) * mid.x + still(vec2(c.x, a.y)) * w3.x) * w0.y +
         (still(vec2(a.x, b.y)) * w0.x + still(vec2(b.x, b.y)) * mid.x + still(vec2(c.x, b.y)) * w3.x) * mid.y +
         (still(vec2(a.x, c.y)) * w0.x + still(vec2(b.x, c.y)) * mid.x + still(vec2(c.x, c.y)) * w3.x) * w3.y;
}

vec4 effect(vec2 uv) {
  // The smooth shapes across and down, and their slopes.
  float across[9];
  float across_slope[9];
  float down[9];
  float down_slope[9];
  vec2 at = uv * 2.0 - 1.0;
  across[0] = 1.0; across[1] = at.x; across_slope[0] = 0.0; across_slope[1] = 1.0;
  down[0] = 1.0; down[1] = at.y; down_slope[0] = 0.0; down_slope[1] = 1.0;
  for (int i = 2; i <= DEGREE; i++) {
    across[i] = 2.0 * at.x * across[i - 1] - across[i - 2];
    across_slope[i] = 2.0 * across[i - 1] + 2.0 * at.x * across_slope[i - 1] - across_slope[i - 2];
    down[i] = 2.0 * at.y * down[i - 1] - down[i - 2];
    down_slope[i] = 2.0 * down[i - 1] + 2.0 * at.y * down_slope[i - 1] - down_slope[i - 2];
  }
  // How far out among the folds this place is, and which way is across them.
  float fold = 0.0;
  vec2 slope = vec2(0.0);
  int k = 0;
  for (int i = 0; i <= DEGREE; i++) {
    for (int j = 0; j <= DEGREE - i; j++) {
      fold += FOLD[k] * across[i] * down[j];
      slope += FOLD[k] * vec2(across_slope[i] * down[j] / aspect, across[i] * down_slope[j]);
      k++;
    }
  }
  vec2 way = slope / max(length(slope), 0.000001);

  // Near each edge of the picture only the motion across that edge fades, so a fold slides along
  // the edge and nothing is read from outside the picture.
  float margin = 10.0 * amount;
  vec2 from_edge = min(uv, 1.0 - uv) * vec2(aspect, 1.0);
  way *= smoothstep(0.0, margin, from_edge);

  // The flat inside of the opening stays put; the folds from its rim outward move.
  float reach = smoothstep(0.8, 1.0, length((uv - OPENING_AT) / OPENING_SIZE));
  float turn = TURN * fold / wave;
  float shift = amount * reach * (sin(turn - TURN * phase) - sin(turn));
  vec2 from = uv - shift * way * vec2(1.0 / aspect, 1.0);
  // Where a fold has not moved at all, the still as it is: at the start of the cycle that is
  // everywhere. A twentieth of a pixel away it is read the crisp way already.
  return mix(still(from), crisp(from), clamp(20.0 * abs(shift) / pixel.y, 0.0, 1.0));
}
