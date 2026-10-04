# Research: Liquid Glass for Quickshell widgets

> Update, 2026-10-03: the Omarchy integration now requests per-region blur with
> `BackgroundEffect`, paints a translucent rim in Quickshell and refracts the
> desktop across each rim with a Hyprland `screen_shader`. The text below records
> the original research and plan; the decision to use `ShaderEffectSource` with a
> gradient as the hosts' material was superseded. See
> [implementation.md](implementation.md) for the current state and
> [compositor-refraction.md](compositor-refraction.md) for the investigation of
> refracting the real desktop.

**Revision date:** 2026-10-03
**Decision:** build a reusable material in the Quickshell shell and validate it
first on the bar and on a real panel. Refraction of the desktop windows behind
the shell remains a separate capability, which needs a pixel source from before
the shell itself is composited.
**State of the evidence:** documentation and code analysis; no new benchmark or
integration was run in this revision.

## Question and scope

How can a surface inspired by Apple's Liquid Glass be applied to the widgets of
the **whole shell**, with a shader running on the GPU, without cloning every
plugin? Here "above the widgets" means a visual language shared by the set of
widgets. Within each control, the material must sit **behind the text, icons and
interactive area**. Drawing a capture of the widgets on top of them would
distort the content and could hurt legibility.

The project is a QML/GLSL prototype for Quickshell on Omarchy. The inspected
reference is commit `d255288`. At the time of this revision, `LiquidGlass.qml`,
`shaders/glass.frag`, `Panel.qml`, `Preview.qml`, the tests and the commit's
documentation were **removed from the working tree**; they were read with
`git show HEAD:<file>`. This research neither restores those files nor changes
the installed shell. The local installation provides Quickshell 0.3.1 and `qsb`
6.11.2. `hyprctl version` could not reach the socket during this revision, so
there is no current confirmation of the running compositor.

Decision criteria, set before any pilot: (1) a common material without copying
each widget's code; (2) content and interaction preserved; (3) a defined
background source without feedback; (4) cost measured against the current look;
(5) an opaque fallback and maintenance proportional to the visual gain. The cost
of getting it wrong includes unreadable text, noticeable latency, continuous GPU
use and an architecture that cannot be maintained across updates.

## Hypotheses and the evidence that would tell them apart

| Hypothesis | Current state | Result that would weaken it |
|---|---|---|
| H1: `ShaderEffect` and `ShaderEffectSource` are enough to refract a known QML source | Supported by the Qt API and the commit's prototype; general integration pending | Visual failure or excessive cost on a real panel with an animated background |
| H2: a single QML layer can automatically refract everything behind every shell window | Not supported: the documented inputs do not provide the compositor scene from before each surface | A proven protocol or API that delivers that buffer, excludes the shell itself and keeps synchronization |
| H3: integrating at the host points avoids cloning plugins | Supported for widgets that go through the bar host; panels with their own `PanelWindow` still need work | A hosted widget that cannot use the material without changing its implementation |
| H4: the integrated GPU keeps an acceptable cost across several containers | Open; only an analytic count of pixels and textures exists | A representative measurement above the frame budget, or an unacceptable energy increase |
| H5: visual similarity to Apple improves the experience | Open; Apple describes properties and uses, without publishing its shader or measuring these users' preference | A comparative test where plain blur is preferred or makes the controls more legible |

## Platform foundations and limits

Qt's [`ShaderEffectSource`](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html)
rasterizes a QML `sourceItem` into a texture; `live` updates it when the source
changes. The documentation warns that this adds video memory use and usually
reduces performance. A recursive dependency needs another texture and, with
`live`, can keep rendering continuously.
[`ShaderEffect`](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html) applies
the shader to the item's geometry; in Qt 6 it uses a `.qsb` file, and the
software backend does not run the effect. These are properties of the Qt scene,
not an API for reading the compositor's framebuffer.

[Quickshell 0.3.1's `ScreencopyView`](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/)
takes a monitor or a window as `captureSource`, subject to the available
protocols. Its API does not document a capture of "every pixel behind this
surface, excluding this surface". **Inference:** a live capture of a monitor
applied over that same monitor can produce feedback or delay; a specific
experiment would be needed to know the local behaviour. A capture of a single
window does not represent every surface behind a panel either.

Quickshell's [`QsWindow`](https://quickshell.org/docs/v0.3.1/types/Quickshell/QsWindow/)
offers `contentItem`, an input mask and per-window scale. This helps compose the
material **inside** each window, without creating an overlay window that covers
the whole screen. The mask handles clickable regions; it does not provide
background pixels. Since the installed Omarchy shell creates the bar in
`/usr/share/omarchy/shell/plugins/bar/Bar.qml:1234` and loads panels in
`/usr/share/omarchy/shell/shell.qml:1293`, there is no single visual tree that a
`ShaderEffectSource` could wrap. Each bar module's slot is in `Bar.qml:1773`;
panels can create their own surfaces.

The Khronos GLSL [`refract`](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html)
function grounds the ray direction at an idealized interface. The commit's
shader uses a synthetic normal at the edge, `eta = 1/ior` and a pixel
displacement proportional to `thickness × ray.xy / -ray.z`
(`shaders/glass.frag:23-42`). `ior`, effective thickness, normal and light are
artistic parameters, not measurements of Apple's material.
[Apple's Liquid Glass presentation](https://developer.apple.com/videos/play/wwdc2025/219/)
supports the inspiration in lensing, adaptation, highlights, interaction and
legibility as a priority; it does not allow a claim of equivalent
implementation.

## Review of the existing implementation

The commit's flow: explicit QML background → local or shared
`ShaderEffectSource` → sampling in the shader → rounded surface → the widget's
content drawn in front. `LiquidGlass.qml:41-56` picks the source and the crop;
`:72-105` instantiates the effect and the capture; `:108` keeps the content in a
later item. `shaders/glass.frag:22-59` computes the mask, normal, refraction, one
texture sample, colour and alpha. `Panel.qml:17-32` only presents the preview in
a `PanelWindow`. The commit's manifest registers that panel, not a global shell
extension.

**Choices that make sense:** content separate from the shader; a texture that
several containers in the same scene can share; an opaque fallback; bounded
parameters; no graphics dependency beyond Qt and Quickshell. The commit's
preview and `tests/render.qml` record optical controls and image comparisons,
but the tests were not repeated in this revision because the files are missing
from the working tree. The accounts in `docs/tese.md` are project history, not a
new independent measurement.

**Confirmed limits:** `sourcePosition` subtracts `x/y` of siblings without
transforms (`LiquidGlass.qml:50-56`); it is not a general mapping between items
or windows. The local source uses a fixed 130 px margin around each container
(`:49-56`), regardless of the effective displacement. The shader clamps UVs to
`[0,1]` (`glass.frag:42`), which can stretch pixels at the edge when the crop
does not cover a sample. `sharedSource` removes duplicated local textures for a
common QML region, but it neither joins the shapes nor crosses Wayland windows.
These are correctness or scale limitations under certain layouts, not measured
bottlenecks.

## Algorithmic and resource model

Let `N` be the number of containers, `Aᵢ = WᵢHᵢ` their areas in logical pixels,
`D` the physical scale per axis, `F` frames per second, `P` the local texture's
logical margin and `S` texture samples per covered fragment. The current shader
has `S = 1` and roughly `Θ(D² ΣAᵢ)` work per frame, plus the pass that generates
the textures and the composition. The pass reads roughly `F S D² ΣAᵢ` samples
per second. One local source per container holds at least
`4D² Σ(Wᵢ+2P)(Hᵢ+2P)` bytes in RGBA8, without MSAA, temporary buffers, alignment
or copies. A shared QML source of area `B` trades that for roughly `4D²B` bytes,
plus each container's separate pass. Sharing only pays off if the common area
and its update rate justify the crop; invalidating it can also redraw regions
that did not change.

Local count reproduced in this revision with Python arithmetic: six `360×180`
containers, `D=2`, `F=60` produce **93,312,000 fragments/s** in the effect pass.
With `P=130`, six local sources add up to **24.98 MiB** in RGBA8; a shared
`640×480` region uses **4.69 MiB**. These are synthetic scenarios at the
preview's size, not estimates of milliseconds, power draw or total memory. The
capture cost can dominate: Qt's
[performance guidance](https://doc.qt.io/qt-6/qtquick-performance.html)
recommends measuring the `ShaderEffectSource` pre-render and the per-pixel
shader.

Algorithmic priorities: (1) avoid capturing the same region several times;
(2) render only visible surfaces and update static backgrounds on demand;
(3) bound the captured area with a margin derived from the largest allowed
displacement plus a filtering guard; (4) only then tune shader instructions or
resolution. A smaller margin without proof of coverage trades memory for
artefacts. None of these changes has a measured gain in this project.

## Candidate architecture for the whole shell

1. Keep **a single material**, QML + `.qsb`, with a contract for source,
   geometry, interaction state, accessibility and fallback.
2. On the bar, integrate the visual layer in the surface's host and in the
   existing `ModuleSlot`s, keeping their `Loader`, IPC, focus and draw order.
   Several slots in the same window can read a texture shared from the available
   QML source; they must not capture an ancestor that includes the glass itself.
3. For panels, use a common host component when creating new `PanelWindow`s and
   adapt the existing panels that create their own windows. Changing only the
   `Loader` at `shell.qml:1335` does not automatically wrap the visual content of
   the windows that plugins create. Shell coverage must be inventoried **per
   surface**, including popups and overlays, before calling it global.
4. In each window, compose in this order: known background → refractive
   material → icons, text and controls. Keep inputs and clickable regions. If
   the real background is not available, use an opaque surface or a stylized
   look that is explicitly labelled as such.
5. If refracting desktop applications is a requirement, investigate an
   integration that hands the shell the pre-composition buffer, together with
   coordinates, scale, synchronization and exclusion of the surface itself.
   Without that proof, do not base the architecture on screencopy. The
   compositor's native blur remains the simplest comparison for that visual
   requirement.

This architecture needs changes at the shell's host points; it does **not**
propose cloning plugins. It also does not promise to apply the material to
independent Quickshell windows that do not adopt the common contract. A
full-screen overlay window does not by itself turn its pixels into a
pre-composition source either.

## Comparison and validation plan

| Option | Real desktop background | Reuse across the shell | Main cost or risk | Decision |
|---|---|---|---|---|
| Compositor transparency and blur | Yes, per the compositor's configuration | Per surface or layer | No geometric refraction from the shader | Baseline |
| QML shader with a known source | Only the supplied source | High at the integrated hosts | Extra capture, cropping and window coverage | **Recommended pilot** |
| Monitor screencopy + shader | Monitor capture | Possible, not yet shown | Feedback, delay, exclusion and scale | Do not adopt without a discriminating experiment |
| Compositor pre-composition source | Potentially yes | Depends on the interface with the shell | Compositor development and maintenance | Separate research if the real desktop is a requirement |

**Proposed pilot, not yet run:** integrate a bar and a panel with an animated
QML background; compare, in alternating order, (A) the current look or blur,
(B) the material with local capture and (C) the material with shared capture,
keeping geometry, content, scale and hardware the same. Measure p50/p95 frame
time, GPU memory use when available, dropped frames, update rate at rest, and
behaviour with 1 and 6 containers at scales 1 and 2. Record the GPU, versions,
resolution, Qt backend and load. Initial criterion **chosen for the pilot**,
open to revision before the results: p95 increase ≤2 ms at 60 Hz, no feedback
or artefacts, and text as legible as the baseline. Test hover, click, hidden
panels, light and dark backgrounds and the fallback; the contrast check must
include the pixels actually presented, per
[WCAG 2.2, 1.4.6](https://www.w3.org/TR/WCAG22/#contrast-enhanced). A
screenshot and the shader's optical test do not replace these measurements.

For the real-desktop hypothesis, first build a minimal proof with one
Quickshell surface and a moving window behind it: check that the received
source excludes the surface itself on every frame, keeps alignment under scale
and movement, and adds no noticeable delay. If any condition fails, keep that
capability out of the QML scope. No such experiment was run here.

## Engineering decision

| Priority | Action | Evidence and expected benefit | Verification |
|---|---|---|---|
| High | Restore or locate the implementation before building; integrate the material in the bar host and in one panel | The commit has the component, the working tree does not; the preview does not cover real widgets | Both use the same component, with no per-plugin copy |
| High | Define the source per window and prevent recursive dependencies | The Qt API captures only `sourceItem`; recursion can force continuous rendering | Animated background without feedback; no unnecessary updates at rest |
| Medium | Replace the position with a correct mapping and bound the crop with proof | The current calculation assumes siblings without transforms; the local margin costs memory | Tests with displacement, scale and edges without visible clamping |
| Experimental | Get a pre-composition background from the compositor | The only path identified for reliable refraction of the real desktop | Minimal proof with exclusion, synchronization and measured cost |

**Conditional conclusion:** apply the material in the shell for known QML
backgrounds, with a pilot and a fallback. Do not describe the result as
refraction of the real desktop or as an implementation equivalent to Apple's.
The factor most able to change the architecture is the proven existence of a
suitable pre-composition source. The research examined the commit, relevant
paths of the installed shell and primary documentation from Qt, Quickshell,
Khronos and Apple; it stopped once the pilot choice was supported. Compatibility
with other versions, performance and user preference remain open.

## Sources and traceability

Sources accessed on **2026-10-03**. The Qt pages opened in this revision describe
Qt **6.12**, while the installed `qsb` is **6.11.2**; matching the local
behaviour exactly needs testing. Page update dates, when not shown, are unknown.

| Source | Part used | Role and limit |
|---|---|---|
| [Qt, ShaderEffectSource](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html) | Detailed Description; `sourceItem`, `live`, `recursive`, `sourceRect` | Contract of the QML capture and cost warnings; does not measure this shell |
| [Qt, ShaderEffect](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html) | Shaders; backend support | Qt 6 shader contract; does not confirm this GPU |
| [Qt, Performance](https://doc.qt.io/qt-6/qtquick-performance.html) | Shader Effects | Guidance for measuring capture and fragments |
| [Quickshell 0.3.1, ScreencopyView](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/) | `captureSource`, `live` | Documented inputs; the lack of an exclusion guarantee is a documentation limit |
| [Quickshell 0.3.1, QsWindow](https://quickshell.org/docs/v0.3.1/types/Quickshell/QsWindow/) | `contentItem`, `mask`, `devicePixelRatio` | Per-window surface, input and scale |
| [Khronos, GLSL 4.60](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html) | the `refract` function | Mathematical basis of an interface, not of Apple's material |
| Installed Omarchy | `shell.qml:1293-1365`; `plugins/bar/Bar.qml:1234-1284,1773-1872` | Local evidence of the host points; can change with an update |
| Commit `d255288` | `LiquidGlass.qml`, `shaders/glass.frag`, `Panel.qml`, `tests/render.qml`, `docs/tese.md` | Historical implementation and tests; files missing from the current working tree |
