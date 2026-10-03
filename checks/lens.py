"""Check how the lens helper places glass rectangles on the screen."""

import importlib.util
import os
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "lens", Path(__file__).parents[1] / "integrations/omarchy/lens.py")
lens = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lens)

pid = os.getppid()
monitor = {"name": "eDP-1", "x": 0, "y": 0}
bar = {"pid": pid, "x": 0, "y": 0, "w": 1920, "h": 30, "level": 2}
popup = {"pid": pid, "x": 1500, "y": 40, "w": 300, "h": 200, "level": 3}
twin = dict(popup, x=100)
module = {"screen": "eDP-1", "window": [1920, 30], "rect": [9, 0, 32, 30], "radius": 8}
card = {"screen": "eDP-1", "window": [300, 200], "rect": [10, 10, 280, 180], "radius": 12}

assert lens.place([module, card], set(), monitor, [bar, popup]) == [
    (9, 0, 32, 30, 8), (1510, 50, 280, 180, 12)]
assert lens.place([card], set(), monitor, [popup, twin]) == [], "ambiguous window was placed"
assert lens.place([module, card], {"eDP-1"}, monitor, [bar, popup]) == [
    (1510, 50, 280, 180, 12)], "bar lens drawn over a fullscreen window"
assert lens.place([module], set(), monitor, [dict(bar, pid=pid + 1)]) == [], "foreign layer matched"
assert "const int COUNT = 2;" in lens.shader_source([(9, 0, 32, 30, 8), (1510, 50, 280, 180, 12)], 1920, 1080)
print("PASS: lens rectangles placed; ambiguous, foreign and covered layers skipped")
