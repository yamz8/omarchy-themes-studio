// A wave of light crosses the wireframe mountains, from the far ridge towards
// the viewer. Each place lights up once in the cycle: its lines glow, then fade.
//
// The area's shape says where the light falls and how much. `when` says at
// which moment of the cycle it is at its height in a place, and the light comes
// up and goes down around that moment as a bell, the same everywhere. cut.py
// measured all three from the still's shipped loop, and wrote this file.

uniform float amount; // how much light the brightest place gets, as a share of white

const float FRAMES = 92.0; // the cycle, in the frames the times below are counted in
const float SPREAD = 5.2; // how wide the bell of light is, in frames

// The frame at which the light is at its height at a place: a polynomial of how
// far across from the middle it is, and how far down from 0.7 of the height.
float when(vec2 uv) {
  float u = uv.x - 0.5;
  float v = uv.y - 0.7;
  return 29.987 * 1.0 +
         211.02 * v +
         245.79 * v * v +
         -1635.0 * v * v * v +
         903.46 * v * v * v * v +
         -5.9306 * u +
         9.9926 * u * v +
         8.7664 * u * v * v +
         794.3 * u * v * v * v +
         135.76 * u * u +
         -480.31 * u * u * v +
         1346.0 * u * u * v * v +
         34.119 * u * u * u +
         -108.94 * u * u * u * v +
         -151.79 * u * u * u * u;
}

vec4 effect(vec2 uv) {
  vec3 colour = still(uv).rgb;
  // Frames since the light was at its height here, in whichever turn of the
  // cycle is nearest, so the end of one turn runs into the start of the next.
  float since = phase * FRAMES - when(uv);
  since -= FRAMES * floor(since / FRAMES + 0.5);
  float light = amount * exp(-0.5 * since * since / (SPREAD * SPREAD));
  // A white with a little less red in it, which adds less to a colour the
  // fuller that colour already is.
  return vec4(colour + light * vec3(0.75, 1.0, 1.0) * (1.0 - colour * colour * colour), 1.0);
}
