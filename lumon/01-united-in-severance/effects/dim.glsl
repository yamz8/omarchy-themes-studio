// The words dim and come back, once in each cycle. UNITED IN sinks to two
// thirds of its light as one; SEVERANCE goes down to half letter by letter,
// left to right, and comes back the same way. A letter dims towards the
// ground just above it, so it fades into the picture and not to black.
//
// Where the letters are comes from the still; when each goes and comes back
// was measured from the loop this scene stands in for, by measure.py.

// The left edge of each letter of SEVERANCE and the right edge of the last,
// as shares of the still's width. What is left of the first is UNITED IN.
const float LETTER[10] = float[10](0.4961, 0.5059, 0.5148, 0.5253, 0.5342, 0.5440, 0.5549, 0.5654, 0.5754, 0.5846);

const float ABOVE = 0.0208;  // how far above a place the ground is taken from, as a share of the height: clear of the letters
const float LOW_WORDS = 0.655;
const float LOW_LETTER = 0.50;
const float FIRST_DOWN = 5.23; // seconds into the cycle the first letter is halfway down
const float FIRST_UP = 8.11;   // and halfway back
const float APART = 0.18;      // seconds from one letter to the next

vec4 effect(vec2 uv) {
  vec4 here = still(uv);
  float now = phase * seconds;
  float left = 1.0;
  if (uv.x < LETTER[0]) {
    left = 1.0 - (1.0 - LOW_WORDS) * (smoothstep(5.06, 6.98, now) - smoothstep(8.07, 9.99, now));
  } else if (uv.x < LETTER[9]) {
    float which = 0.0;
    for (int i = 1; i < 9; i++) which += step(LETTER[i], uv.x);
    float down = FIRST_DOWN + APART * which;
    float back = FIRST_UP + APART * which;
    left = 1.0 - (1.0 - LOW_LETTER) * (smoothstep(down - 0.21, down + 0.21, now) - smoothstep(back - 0.30, back + 0.30, now));
  }
  if (left >= 1.0) return here;
  vec4 ground = still(vec2(uv.x, uv.y - ABOVE));
  return vec4(mix(ground.rgb, here.rgb, left), 1.0);
}
