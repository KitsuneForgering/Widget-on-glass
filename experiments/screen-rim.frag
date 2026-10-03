#version 300 es
// Experimental compositor lens for the centered menu on a 1920x1080 screen.
// The screen shader sees the final frame, so only sample across the card edge.
precision highp float;

in vec2 v_texcoord;
layout(location = 0) out vec4 fragColor;
uniform sampler2D tex;

void main() {
    vec2 screen = vec2(textureSize(tex, 0));
    vec2 p = v_texcoord * screen - screen * 0.5;
    vec2 halfSize = vec2(175.0, 352.0);
    float radius = 8.0;
    vec2 q = abs(p) - (halfSize - radius);
    float d = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
    vec2 outside = max(q, 0.0);
    vec2 normal = length(outside) > 0.0
        ? normalize(outside) * sign(p)
        : (q.x > q.y ? vec2(sign(p.x), 0.0) : vec2(0.0, sign(p.y)));
    vec4 original = texture(tex, v_texcoord);
    if (d > -10.0 && d < 2.0) {
        float edge = smoothstep(-10.0, -5.0, d) * (1.0 - smoothstep(-5.0, 2.0, d));
        vec2 displaced = clamp(v_texcoord + normal * (10.0 - d) / screen, 0.0, 1.0);
        fragColor = mix(original, texture(tex, displaced), 0.28 * edge);
    } else {
        fragColor = original;
    }
}
