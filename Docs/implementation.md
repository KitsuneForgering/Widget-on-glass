# Omarchy integration: verifiable state

## Standalone demo

```sh
bash build.sh run
```

This compiles the shaders, lints the QML and opens the small demo shell in
`src/`. The demo draws its own QML backgrounds and does not replace the Omarchy
shell. To check the refractive shader on that synthetic background, run
`bash build.sh render-check`; the test does not prove refraction of the real
desktop.

The prototype `src/GlassWidget.qml` still demonstrates refraction of a **QML
texture supplied by the host**. Its graphical test checks only that case. It
does not refract the desktop and the Omarchy adapter does not use it.

## The adapter

`integrations/omarchy/apply.py` adds `GlassOverlay.qml` to the default bar,
`KeyboardPanel`, the menu, clipboard and emoji cards, popup notifications,
`PopupCard` and the OSD. It makes those hosts' backgrounds transparent, compiles
a shader for the material and uses Quickshell's `BackgroundEffect.blurRegion` to
request blur only behind each host's region. On this path **Hyprland samples the
real desktop** and performs the blur. The base uses each surface's own theme
colour at 75% opacity. The adapter draws menu and clipboard secondary text fully
opaque to keep its contrast. A second instance of the shader paints a reflection
and a narrow highlight along the top of the edges, without accepting input.

The menu, clipboard and emojis draw a full-screen veil. Their blur request uses
`Region { item: card; radius: card.radius }`. The notification region is the
column of cards, so the gaps between cards can also be blurred.

Inner containers use the same material. The adapter adds a `Loader` to
`BorderSurface` that loads a rim light with lens whenever the surface has a
fill; this covers selected rows, device chips, buttons and other panel states
without changing each plugin. Clipboard and emoji rows and the highlights of
`Dropdown`, `SearchableDropdown` and `MultiSelect` are `Rectangle`s and get the
same rim directly. Those dropdowns' popups and the `ConfirmDialog` card, which
were opaque, use the glass base and reflection. The full-screen veil of the
menu, clipboard and emojis is now `GlassScrim`, a `Shape` with a rounded hole
under the card; before, the veil also darkened the glass. Items clipped by a
list with `clip` send only their visible part to the lens.

`PopupCard` uses the shared material too, covering popups such as media, tray
and plugin previews. The local `tornikegomareli.spaces` plugin drew an almost
opaque fill in its preview; the reload makes it transparent and keeps a backup.
Feader RSS uses `KeyboardPanel` and gets the material without code changes.

This is a working approximation, not a faithful reproduction of Apple's Liquid
Glass. Every base `GlassOverlay` registers with the `GlassLens` singleton. Every
300 ms, or right after a visibility change, the singleton collects the visible
rectangles in window coordinates and calls the `bin/widget-on-glass-lens` helper
only when the set changed. The helper finds each window in Hyprland's layer list
(same PID and size) and generates a single `screen_shader` with the rim lens of
every surface. The rim band scales with the surface: 10 px on large cards, about
3 px on bar modules. The lens runs only on a single unrotated monitor and only
when no other `screen_shader` is configured. While a window is fullscreen,
surfaces below the overlay layer leave the lens. It is resent after
`hyprctl reload` and after changes to `shell.json`, and it is replaced or
cleared when the shell starts again. The lens does not recover the background
hidden behind the centre of a surface; blending or morphing between surfaces
and a complete legibility evaluation are also still open. The
[material Apple describes](https://developer.apple.com/videos/play/wwdc2025/219/)
combines those properties. Qt's `ShaderEffectSource` does not deliver desktop
pixels from before composition.

## Install or apply to a source checkout

`./install.sh` detects the Omarchy package version, clones the official
`v<version>` tag, applies the adapter, calls `omarchy dev link --no-reboot` and
reloads the shell in the current Hyprland session. `./install.sh --prepare-only`
creates the checkout without changing the system link. `./install.sh
--reload-only` reloads an already linked checkout without running `sudo` again.
The reload updates `OMARCHY_PATH` in both Hyprland and the user service manager,
stops the old shell and calls `omarchy restart shell`. It checks the IPC ping and
restores the previous path on failure. It does not reload a locked session. A
later reboot moves the remaining session processes as well.

On 2026-10-03, the first version of the reload started
`quickshell -n -p ~/.local/share/widget-on-glass/omarchy-v4.0.4/shell` and the
IPC ping answered `ok`, but Hyprland's keybindings still used the previous path
and failed. The packaged shell was restored while the activation was fixed.

```sh
python3 integrations/omarchy/apply.py /path/to/omarchy-source-checkout
```

The script expects the Omarchy layout observed on 2026-10-03 and fails when
code anchors differ. It edits the bar, keyboard panel, menu, clipboard, emoji
and notification hosts plus `shell/Ui/qmldir`, and copies the component, the
`GlassLens` singleton, the shaders and the lens helper into the checkout. It
refuses `/usr/share/omarchy`. On checkouts from earlier versions, `--refresh`
removes the menu-only lens and the unused `GlassAppearance.qml` and
`GlassBackdrop.qml`, and moves launchers from earlier opacities to 75%.

`bar.glassEnabled: false` in `shell.json` turns off the material and the blur
request on the bar and `KeyboardPanel`; the other hosts do not expose that
option yet. `bar.glassReducedTransparency` and `bar.glassHighContrast` are
manual options for those two hosts only. They are not connected to the system's
accessibility preferences. The rim lens is global: any of those three options,
or `bar.glassLens: false`, turns the lens off on every surface.

## Marketplace plugin

A third-party plugin cannot reach the shell's own surfaces: third-party services
are created without a visual parent, and visual plugins only reach their own
window's item tree. What a plugin may do is replace whole surfaces of `kind: bar`
and `kind: menu`. `integrations/marketplace/build.py` builds the
[omarchy-glass](https://github.com/KitsuneForgering/omarchy-glass) plugin from
that: it applies `apply.py` to a scratch copy of the stock shell, extracts the
patched `Bar.qml` and `Menu.qml`, renames the glass components to `PluginGlass*`
so they cannot collide with an installer checkout, and adds a menu button
widget. Omarchy does not ship Python, so the plugin's lens
(`integrations/marketplace/PluginGlassLens.qml`) queries Hyprland and writes
the shader from QML. The stock tray reserves its full drawer width; since the
plugin cannot patch `Tray.qml`, its bar shrinks the tray slot by the hidden part
instead.

Checked on 2026-10-03 on the stock 4.0.4 shell: `omarchy plugin validate`
passes; `omarchy plugin add <repo> --enable` makes the glass bar active and
turns the lens on (14 rectangles at rest, 16 with the menu open);
`omarchy plugin remove` restores the built-in bar and clears the shader. The
tray slot was checked collapsed and with `expanded` forced on; hovering it with
a real pointer was not tested, because warping the cursor with Hyprland's
dispatcher did not produce hover events. Changes to a plugin's bar file only
take effect after `omarchy restart shell`.

During one `omarchy plugin add --enable`, the stock shell crashed with SIGSEGV
in Quickshell's native code (`__dynamic_cast`) while finalizing an object
created by an asynchronous incubator; the shell restarted normally. The host
loads third-party bars with an asynchronous `Loader`, and the git clone
triggered several plugin reloads in a row, so a race in Quickshell or the host
is the likely trigger. Quickshell's frames had no debug symbols, so the failing
type is unknown. Two other enables did not crash.

## Coverage and next criteria

The default bar, `KeyboardPanel`, the menu, clipboard, emojis, popup
notifications and the OSD are integrated. The image picker, the lock screen,
other `PanelWindow`s and alternative bars do not use the material yet. Widgets
that draw opaque backgrounds also hide the host's material. The integration
cannot be called global yet.

The local Hyprland 0.56.2 implements `ext-background-effect-v1` and has blur
enabled, but does not expose `decoration:blur:variant`; the `acrylic` variant
from newer documentation is not available here. Refracting the whole area
behind a surface needs a change to Hyprland's composition stage, or a future
API that applies refraction to the image behind each layer with correct
geometry, scale and synchronization. Until then, the real desktop gets blur,
rim light and the narrow rim lens.

Validation done: shaders compiled with `qsb`, QML checked with `qmllint`, the
refresh applied to a temporary copy of the prepared checkout, the shell
restarted with an IPC ping and screenshots taken in the Wayland session. The
contrast check covers opaque text on representative light and dark palettes
over any grey backdrop; it does not cover every theme or widget state, and
dimmed labels drawn by stock panel widgets can fall below 4.5:1 over very
bright backdrops. `checks/lens.py` checks how the helper places rectangles,
including ambiguous windows, layers of other processes and fullscreen. The lens
cost measurement is in [compositor-refraction.md](compositor-refraction.md).
Visual inspection of every panel, energy measurements and complete
accessibility testing are still missing.
