"""Check that refraction affects the rim while leaving the flat center stable."""

from pathlib import Path
import subprocess


images = [Path(f"/tmp/widget-on-glass-pilot-{n}.png") for n in (0, 1)]
for image in images:
    if not image.is_file():
        raise SystemExit(f"missing render: {image}")


def signature(image: Path, crop: str) -> str:
    return subprocess.check_output(
        ["magick", str(image), "-crop", crop, "+repage", "-format", "%#", "info:"],
        text=True,
    )


assert signature(images[0], "200x80+220+140") == signature(images[1], "200x80+220+140"), (
    "flat center changed when only thickness changed"
)
assert signature(images[0], "50x80+85+140") != signature(images[1], "50x80+85+140"), (
    "rim did not refract when thickness changed"
)
print("PASS: refracted rim changed; flat center stayed identical")
