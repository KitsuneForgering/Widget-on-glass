"""Independent optical checks and transparent capacity arithmetic; stdlib only."""
from math import asin, cos, degrees, isclose, radians, sin, sqrt
import subprocess
import sys


def refract(incident, normal, eta):
    dot = sum(i * n for i, n in zip(incident, normal))
    k = 1 - eta * eta * (1 - dot * dot)
    if k < 0:
        return (0, 0, 0)
    return tuple(eta * i - (eta * dot + sqrt(k)) * n
                 for i, n in zip(incident, normal))


for angle in (0, 15, 30, 60, 80):
    incident = (sin(radians(angle)), 0, -cos(radians(angle)))
    ray = refract(incident, (0, 0, 1), 1 / 1.5)
    # Compare the vector formula against scalar Snell, including normal incidence.
    assert isclose(ray[0], sin(radians(angle)) / 1.5, abs_tol=1e-12)
    assert isclose(sum(x * x for x in ray), 1, abs_tol=1e-12)
    assert ray[2] < 0
assert refract((sin(radians(60)), 0, -cos(radians(60))), (0, 0, 1), 1.5) == (0, 0, 0)
print(f"Snell 30° air→glass, n=1.5: {degrees(asin(sin(radians(30)) / 1.5)):.2f}°")


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground, background):
    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


for foreground, background in (("#172334", "#f5f7fa"), ("#ffffff", "#172334")):
    ratio = contrast(foreground, background)
    assert ratio >= 7, f"WCAG AAA contrast pair failed: {foreground} on {background}: {ratio:.2f}:1"
    print(f"PASS: WCAG AAA label pair {foreground} on {background}: {ratio:.2f}:1")

for foreground, background in (("#172334", "#eef2f6"), ("#172334", "#d7dfe8"),
                               ("#ffffff", "#172334"), ("#ffffff", "#304356")):
    ratio = contrast(foreground, background)
    assert ratio >= 7, f"WCAG AAA preview text failed: {foreground} on {background}: {ratio:.2f}:1"

for dpr in (1, 2):
    pixels = 360 * 180 * 6 * 60 * dpr**2
    print(f"6 cards 360×180 @60 Hz DPR={dpr}: {pixels:,} fragments/s; {pixels*3:,} reads/s if 3 samples")
for width, height in ((1920, 1080), (3840, 2160)):
    print(f"RGBA8 {width}×{height}: {width*height*4/2**20:.2f} MiB/texture")
print("PASS: Snell scalar/vector agreement, unit vectors, total internal reflection")

if "--render" in sys.argv:
    # ImageMagick is already installed on this Omarchy; no Python imaging dependency.
    paths = [f"/tmp/widget-on-glass-render-{i}.png" for i in (0, 1)]
    diff = subprocess.run(["magick", "compare", "-metric", "RMSE", *paths, "null:"],
                          capture_output=True, text=True)
    assert diff.returncode == 1 and float(diff.stderr.split()[0]) > 0, diff.stderr
    sizes = [subprocess.check_output(["magick", "identify", "-format", "%w %h", p], text=True)
             for p in paths]
    assert sizes[0] == sizes[1], "window geometry changed between captures"
    width, height = map(int, sizes[0].split())
    center = f"200x80+{width//2-100}+{height//2-40}"
    signatures = [subprocess.check_output(["magick", p, "-crop", center, "-format", "%#", "info:"], text=True)
                  for p in paths]
    assert signatures[0] == signatures[1], "flat center should have no displacement"
    print(f"PASS: refraction changed edge pixels (RMSE {diff.stderr.strip()}); flat center unchanged")
    for phases, label in [((2, 3), "ior=1: thickness must not change pixels"),
                          ((4, 5), "disabled glass and missing source must use the same opaque fallback")]:
        images = [f"/tmp/widget-on-glass-render-{i}.png" for i in phases]
        control = subprocess.run(["magick", "compare", "-metric", "RMSE", *images, "null:"],
                                 capture_output=True, text=True)
        assert control.returncode == 0, f"{label}: {control.stderr}"
        print(f"PASS: {label}")
    for a, b in ((1, 6), (6, 7), (7, 8), (9, 12), (10, 11)):
        crops = [subprocess.check_output(["magick", f"/tmp/widget-on-glass-render-{i}.png",
                                         "-crop", center, "-format", "%#", "info:"], text=True)
                 for i in (a, b)]
        assert crops[0] == crops[1], f"backdrop text changed in protected center: {a}/{b}"
    for a, b in ((14, 15), (16, 17)):
        parallax_images = [f"/tmp/widget-on-glass-parallax-{index}.png" for index in (a, b)]
        for phase, target in zip((a, b), parallax_images):
            subprocess.run(["magick", f"/tmp/widget-on-glass-render-{phase}.png",
                            "-crop", center, "+repage", target], check=True)
        parallax = subprocess.run(["magick", "compare", "-metric", "RMSE",
                                   *parallax_images, "null:"], capture_output=True, text=True)
        assert parallax.returncode == 1 and float(parallax.stderr.split()[0]) > 0, (
            f"content refraction did not change the readable interior: {a}/{b}")
        print(f"PASS: content refraction changes the interior (RMSE {parallax.stderr.strip()})")
    feedback = subprocess.run(["magick", "compare", "-metric", "RMSE",
                               "/tmp/widget-on-glass-render-7.png", "/tmp/widget-on-glass-render-8.png", "null:"],
                              capture_output=True, text=True)
    assert feedback.returncode == 1, "press feedback did not change material"
    print("PASS: backdrop center preserved with local/shared source, press feedback, white/dark backgrounds")
