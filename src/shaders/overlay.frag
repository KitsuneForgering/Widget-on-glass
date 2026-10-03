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
};

void main() {
    vec2 p = (qt_TexCoord0 - 0.5) * size;
    vec2 q = abs(p) - (size * 0.5 - radius);
    float d = length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - radius;
    float aa = max(fwidth(d), 0.75);
    float coverage = 1.0 - smoothstep(-aa, aa, d);
    float rim = 1.0 - smoothstep(0.0, 3.0, -d);
    float topLight = mix(0.35, 1.0, 1.0 - qt_TexCoord0.y);
    float glow = rim * topLight * (0.32 + activity * 0.10);
    float alpha = coverage * (reflectionOnly > 0.5 ? glow : opacityBase) * qt_Opacity;
    vec3 color = reflectionOnly > 0.5 ? vec3(0.94, 0.97, 1.0) : vec3(0.10, 0.14, 0.19);
    fragColor = vec4(color * alpha, alpha);
}
