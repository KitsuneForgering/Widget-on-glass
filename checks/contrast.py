"""Check representative theme text against the fixed glass over any grey backdrop."""

import re
from pathlib import Path


qml = (Path(__file__).parents[1] / "src/GlassOverlay.qml").read_text()
panel_alpha = float(re.search(r"property real baseOpacity: ([\d.]+)", qml)[1])
bar_alpha = 0.75
adapter = (Path(__file__).parents[1] / "integrations/omarchy/apply.py").read_text()
launcher_alpha = float(re.search(r"LAUNCHER_GLASS = .*baseOpacity: ([\d.]+)", adapter)[1])


def linear(channel):
    channel /= 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def contrast(a, b):
    a, b = sorted((linear(a), linear(b)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# Only opaque text is guaranteed: menu and clipboard secondary text is patched
# to full opacity, while stock panel widgets keep their own dimmed labels.
for alpha, text_alphas in ((bar_alpha, (1.0,)), (launcher_alpha, (1.0,)), (panel_alpha, (1.0,))):
    for surface, text in ((26, 202), (242, 28)):
        for text_alpha in text_alphas:
            worst = float("inf")
            for backdrop in range(256):
                background = surface * alpha + backdrop * (1 - alpha)
                foreground = text * text_alpha + background * (1 - text_alpha)
                worst = min(worst, contrast(foreground, background))
            assert worst >= 4.5, f"theme text falls to {worst:.2f}:1"
            print(f"surface {surface}, glass {alpha}, text {text_alpha}: {worst:.2f}:1")
