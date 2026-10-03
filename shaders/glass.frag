#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
    float radius;
    float bevel;
    float thickness;
    float contentRefraction;
    float ior;
    vec2 sourceExtent;
    vec4 sampleRect;
    float interaction;
    float activeSurface;
    float preserveBackground;
    vec4 tint;
};
layout(binding = 1) uniform sampler2D source;

void main() {
    vec2 p = (qt_TexCoord0 - 0.5) * size;
    vec2 q = abs(p) - (size * 0.5 - radius);
    vec2 outside = max(q, vec2(0.0));
    float d = length(outside) + min(max(q.x, q.y), 0.0) - radius;
    float coverage = 1.0 - smoothstep(-fwidth(d), fwidth(d), d);
    if (coverage <= 0.0) { fragColor = vec4(0.0); return; }

    vec2 gradient = length(outside) > 0.0001
        ? normalize(outside) * sign(p)
        : (q.x > q.y ? vec2(sign(p.x), 0.0) : vec2(0.0, sign(p.y)));
    float slope = 0.7 * (1.0 - smoothstep(0.0, bevel, max(-d, 0.0)));
    float radialDistance = length(p / max(size * 0.5, vec2(1.0)));
    vec2 radialGradient = p / max(length(p), 0.001)
        * (0.32 * contentRefraction * smoothstep(0.0, 1.0, radialDistance));
    vec3 normal = normalize(vec3(gradient * slope + radialGradient, 1.0));
    // Snell at one synthetic interface; thickness is a tunable distance in px.
    vec3 ray = refract(vec3(0.0, 0.0, -1.0), normal, 1.0 / ior);
    vec2 offset = ior == 1.0 ? vec2(0.0) : thickness * ray.xy / max(-ray.z, 0.001);
    vec2 uv = sampleRect.xy + qt_TexCoord0 * sampleRect.zw + offset / sourceExtent;
    vec4 sampleColor = texture(source, clamp(uv, vec2(0.0), vec2(1.0)));
    vec3 rgb = sampleColor.rgb / max(sampleColor.a, 0.0001);
    float rim = 1.0 - smoothstep(0.0, bevel, max(-d, 0.0));
    float material = mix(1.0, rim, preserveBackground);
    // The opt-in radial normal gently lenses the interior; text stays sharp in the source.
    float luminance = dot(rgb, vec3(0.2126, 0.7152, 0.0722));
    float adaptiveTint = clamp(tint.a, 0.0, 0.2) * (0.35 + 0.65 * luminance) * material;
    rgb = mix(rgb, tint.rgb, adaptiveTint);
    float f0 = pow((ior - 1.0) / (ior + 1.0), 2.0);
    float fresnel = f0 + (1.0 - f0) * pow(1.0 - normal.z, 5.0);
    float directional = pow(max(dot(normal, normalize(vec3(-0.6, -0.8, 1.0))), 0.0), 16.0);
    float highlight = (fresnel + directional * 0.12 + interaction * 0.08) * material * activeSurface;
    rgb = mix(rgb, vec3(1.0), clamp(highlight, 0.0, 0.3));
    // Luminance-scaled dark rim; the directional highlight supplies the light edge.
    rgb *= 1.0 - 0.08 * luminance * rim * activeSurface;
    float alpha = mix(sampleColor.a, 1.0, adaptiveTint) * coverage * qt_Opacity;
    fragColor = vec4(rgb * alpha, alpha);
}
