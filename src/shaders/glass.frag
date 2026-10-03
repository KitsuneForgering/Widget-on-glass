#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
    vec2 sourceSize;
    vec4 sampleRect;
    float radius;
    float bevel;
    float thickness;
    float ior;
    float interaction;
};
layout(binding = 1) uniform sampler2D source;

void main() {
    vec2 p = (qt_TexCoord0 - 0.5) * size;
    vec2 q = abs(p) - (size * 0.5 - radius);
    vec2 outside = max(q, vec2(0.0));
    float distanceToEdge = length(outside) + min(max(q.x, q.y), 0.0) - radius;
    float coverage = 1.0 - smoothstep(-fwidth(distanceToEdge), fwidth(distanceToEdge), distanceToEdge);
    if (coverage <= 0.0) {
        fragColor = vec4(0.0);
        return;
    }

    vec2 gradient = length(outside) > 0.0001
        ? normalize(outside) * sign(p)
        : (q.x > q.y ? vec2(sign(p.x), 0.0) : vec2(0.0, sign(p.y)));
    float edge = 1.0 - smoothstep(0.0, bevel, max(-distanceToEdge, 0.0));
    vec3 normal = normalize(vec3(gradient * 0.7 * edge, 1.0));
    vec3 ray = refract(vec3(0.0, 0.0, -1.0), normal, 1.0 / ior);
    vec2 offset = ior == 1.0 ? vec2(0.0) : thickness * ray.xy / max(-ray.z, 0.001);
    vec2 baseUv = sampleRect.xy + qt_TexCoord0 * sampleRect.zw;
    vec2 uv = baseUv + offset / sourceSize;
    if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) uv = baseUv;
    vec4 sampled = texture(source, clamp(uv, vec2(0.0), vec2(1.0)));
    vec3 rgb = sampled.rgb / max(sampled.a, 0.0001);

    float luminance = dot(rgb, vec3(0.2126, 0.7152, 0.0722));
    float f0 = pow((ior - 1.0) / (ior + 1.0), 2.0);
    float fresnel = f0 + (1.0 - f0) * pow(1.0 - normal.z, 5.0);
    float highlight = clamp((fresnel + interaction * 0.12 + edge * 0.09) * edge, 0.0, 0.26);
    rgb = mix(rgb, vec3(1.0), highlight);
    rgb *= 1.0 - edge * 0.06 * luminance;
    float alpha = sampled.a * coverage * qt_Opacity;
    fragColor = vec4(rgb * alpha, alpha);
}
