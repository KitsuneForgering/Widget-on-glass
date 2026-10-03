#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
    float radius;
    float opacityBase;
    float activity;
    float reflectionOnly;
    vec4 tint;
};

void main() {
    vec2 p = (qt_TexCoord0 - 0.5) * size;
    vec2 q = abs(p) - (size * 0.5 - radius);
    float d = length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - radius;
    float aa = max(fwidth(d), 0.75);
    float coverage = 1.0 - smoothstep(-aa, aa, d);
    float bevel = 1.0 - smoothstep(0.0, min(7.0, min(size.x, size.y) * 0.2), -d);
    float rim = 1.0 - smoothstep(0.0, 1.5, -d);
    float light = pow(1.0 - qt_TexCoord0.y, 2.0) * (0.55 + 0.45 * (1.0 - qt_TexCoord0.x));
    float glint = exp(-pow((qt_TexCoord0.y * size.y - 2.0) / 2.0, 2.0))
                * smoothstep(0.05, 0.2, qt_TexCoord0.x)
                * (1.0 - smoothstep(0.55, 0.8, qt_TexCoord0.x));
    float glow = rim * (0.16 + light * 0.32 + activity * 0.10)
               + bevel * light * 0.18 + glint * 0.12;
    float alpha = coverage * (reflectionOnly > 0.5 ? glow : opacityBase) * qt_Opacity;
    vec3 base = tint.rgb / max(tint.a, 0.001);
    base = mix(base, vec3(1.0), 0.035 * (1.0 - qt_TexCoord0.y));
    vec3 color = reflectionOnly > 0.5 ? vec3(0.94, 0.97, 1.0) : base;
    fragColor = vec4(color * alpha, alpha);
}
