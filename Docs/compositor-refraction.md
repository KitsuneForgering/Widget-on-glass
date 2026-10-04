# Refracting the real desktop: investigation and decision

**Revised:** 2026-10-03. **System examined:** Hyprland 0.56.2 (`efb5099`),
Quickshell 0.3.1 and Omarchy installed in `/usr/share/omarchy`. **Revised
decision:** Hyprland's `screen_shader` can displace real pixels at the edge of a
card that is already composited. The adapter now generates a single lens with
the geometry of every visible glass surface on a single monitor; a shader the
user configured is never replaced. Refracting the whole area behind a widget
still needs access to the frame from before the layer is composited. The
adapter's material remains an approximation, not Apple's Liquid Glass.

## Question, hypotheses and criterion

The desired effect must displace **real pixels of the windows and wallpaper
behind** each widget, without including the widget itself in the source, keep
text and icons sharp, and cost little when nothing changes. A minimal proof
needs a reference pattern behind a bar, a measurable displacement of that
pattern only at the card's edge, a stable centre, no recursive copies, and
correct alignment at integer and fractional scale. A QML gradient or a delayed
capture does not meet the criterion.

| Hypothesis | Discriminating prediction | Documented or local result |
|---|---|---|
| `ShaderEffectSource` reads the desktop | A QML source would include outside windows behind the shell | False by contract: the source is a `sourceItem` of the Qt scene. [Qt](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html) |
| `ScreencopyView` provides the buffer from before the shell itself | The API would guarantee a capture without the shell or offer a pre-composition mode | Not documented; it takes a monitor or a toplevel. Capturing the live monitor can feed the effect back into itself. [Quickshell](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/) |
| `no_screen_share` removes the shell from the capture and reveals what is behind | The shell's area would be transparent in the capture | Contradicted by the specification: the hidden layer is replaced with black. [Hyprland, layer rules](https://wiki.hypr.land/configuring/core/rules/layer-rules/) |
| `ext-background-effect-v1` allows refraction | The protocol would return pixels or accept a shader or displacement | False: it only exposes a **blur** region whose technique is compositor policy. [Protocol](https://wayland.app/protocols/ext-background-effect-v1) |
| `screen_shader` can displace pixels at the edge without changing text | A narrow mask applied to the final frame would change the edge and leave the centre identical | Confirmed on a fixed menu at 1920×1080; it does not provide the pixels hidden under the whole card. [Hyprland, official example](https://github.com/hyprwm/Hyprland/blob/v0.56.2/example/screenShader.frag) |
| A Hyprland plugin can change the render stage | There would be a stable shader extension for a layer | Not found in the 0.56.2 API; the API documents function hooks with no stability guarantee. [Hyprland 0.56, development](https://wiki.hypr.land/0.56.0/Plugins/Development/Advanced/), [API](https://github.com/hyprwm/Hyprland/blob/v0.56.2/src/plugins/PluginAPI.hpp) |

The composition model explains both reaches. A QML fragment shader receives the
texture of a Qt item. The `screen_shader` receives the final frame:
`G(x) = F(x + δ(x))`. If `x + δ` falls outside the card, the sample holds the
real desktop; if it falls inside, it holds the card and its content, already
composited. That is why the rim lens works, while refraction of the whole area
the card hides cannot come from a single final pass. That needs the shader to
run **before the layer is composited**, sampling a valid copy of the previous
framebuffer and drawing text and icons afterwards. This last part remains an
architecture proposal.

## Alternatives compared

| Path | Real desktop | Geometric refraction | Cost and limit |
|---|---|---|---|
| `BackgroundEffect.blurRegion` + QML rim shader | Yes, behind the region | No | Existing API, cost limited to the region; chosen as the applicable step |
| `screen_shader` at the rim + `BackgroundEffect` behind the card | Yes, through samples outside the rim | Yes, only in a narrow band | Positive local proof; now integrated with dynamic geometry and measured |
| Monitor screencopy + QML shader | Final capture | Possible, but with feedback and latency | Does not offer the required pre-layer buffer; rejected for general use |
| Plugin with a private hook in Hyprland 0.56.2 | Yes | Potentially | Unstable internal ABI and symbols; a mistake can take down the session. Only justifiable in a nested Hyprland session after a measured prototype |
| Patch to Hyprland's renderer or an upstream API | Yes | Yes, in principle | Most work and maintenance; the correct path for the required optical property |
| `acrylic` variants from newer documentation | Yes | The documentation describes refraction | `hyprctl getoption decoration:blur:variant` answered `no such option` on 0.56.2; unavailable here. [Current configuration](https://wiki.hypr.land/configuring/core/config-options/) |

## What was applied and tested locally

The Omarchy adapter uses
[`BackgroundEffect.blurRegion`](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/BackgroundEffect/)
on every integrated window. The bar uses its window area; `KeyboardPanel`, the
menu, clipboard, emojis and OSD use the card's geometry; notifications use the
column. This replaces the global blur rules and the artificial veil opacity of
the launchers. The `GlassOverlay` shader draws the base behind the content and a
rim reflection above it.

**Local run:** `bash build.sh` passed; `apply.py` applied without errors to a
temporary copy of `/usr/share/omarchy/shell`; a minimal Quickshell window with
`BackgroundEffect.blurRegion` and `GlassOverlay` loaded for two seconds in the
Wayland session. `hyprctl version` confirmed 0.56.2,
`hyprctl getoption decoration:blur:enabled` returned `true`, and
`hyprctl getoption decoration:blur:variant` returned `no such option`. The local
headers include `BackgroundEffect.hpp`. These results confirm the API and that
it loads, **not** the final look or geometric refraction.

**Additional `screen_shader` experiment:** the
[runtime Lua configuration](https://wiki.hypr.land/configuring/core/config-options/)
loaded a temporary shader with
`hyprctl eval 'hl.config({ decoration = { screen_shader = "/path/shader.frag" } })'`.
A red 4% marker in the corner appeared in the `grim` capture, confirming that it
records the result of that pass. With the menu centred at 1920×1080 over a
static background, two consecutive captures gave a mean normalized difference of
0.045 in the top band, 0.032 on the left and 0.035 on the right; the centre and
the outside area gave 0. The first displacement (blend 0.75, 14 px band) created
dark streaks. The smaller variant in
[`experiments/screen-rim.frag`](../experiments/screen-rim.frag) reduced the
blend to 0.28 and the band to 12 px: cleaner, but subtle. Every trial restored
the configuration with `hyprctl reload`; `decoration:screen_shader` went back to
`[[EMPTY]]` and `hyprctl configerrors` stayed empty. This proved the mechanism on
a single card with fixed geometry, not the final visual quality or global
support.

**Current integration:** every base `GlassOverlay` registers with the
`GlassLens` singleton (`src/GlassLens.qml`). It collects the visible rectangles
in window coordinates (`QsWindow.itemRect`) and sends them to the
`integrations/omarchy/lens.py` helper, installed as `bin/widget-on-glass-lens`,
only when the set changes. The helper adds each window's origin, found in
`hyprctl layers` by the shell's PID and the window size, and writes a shader with
up to 32 rectangles. The file name is a hash of the content, so Hyprland
recompiles on every change. A window whose size matches another one at a
different origin stays out of the lens. While a window is fullscreen,
rectangles in layers below the overlay layer leave the lens too. The helper
only proceeds with a single unrotated monitor and with `screen_shader` empty or
already pointing at one of its own shaders. The earlier menu-only version was
removed. The marketplace plugin uses the same logic written in QML
(`integrations/marketplace/PluginGlassLens.qml`), because Omarchy does not ship
Python.

**Live validation (2026-10-03, eDP-1 1920×1080, scale 1):** at rest, the shader
received 15 rectangles whose positions match the bar modules in the `grim`
capture, with no text distortion. Opening the menu raised it to 16 and closing
it went back to 15. Switching a window to fullscreen cleared `screen_shader`;
leaving fullscreen brought the lens back. `hyprctl reload` reset the shader, and
the `configreloaded` event restored it in under 1 s. `bar.glassLens: false` in
`shell.json` cleared the lens, and restoring the file turned it back on.
Killing the shell leaves the last shader active until the next start, which
replaces or clears it. `hyprctl configerrors` stayed empty.

**Cost (same machine, Iris Xe TigerLake, 15 rectangles):** GPU busy time,
measured from the i915 RC6 residency, and Hyprland's CPU time were sampled in
three 5 s rounds with the lens on and off. With the desktop at rest, the GPU was
24–29% busy with the lens and 24–26% without it. With a square spinning at
60 Hz in the corner, it was 22–35% with the lens and 24–32% without it.
Hyprland's CPU ranged from 6% to 21% in both cases. There was no difference
above the noise, which came from another workload in the session. The test does
not measure per-frame latency or energy (RAPL needs root), and does not cover
high-resolution or fractionally scaled screens.

The remaining limit is access to the pre-layer framebuffer for a full-area lens.
Apple describes lensing, adaptation and blending, but does not publish the
internal shader; even a correct refraction of the desktop would not prove
equivalence to the proprietary material.
[Apple, Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/)
