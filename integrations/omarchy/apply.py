"""Apply the compositor-backed glass pilot to an Omarchy source checkout.

Usage: python3 integrations/omarchy/apply.py /path/to/omarchy
The checkout must match the shell layout inspected on 2026-10-03.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PROJECT = Path(__file__).resolve().parents[2]


def replace_once(source: str, before: str, after: str, path: Path) -> str:
    if source.count(before) != 1:
        raise ValueError(f"expected one anchor in {path}: {before[:70]!r}")
    return source.replace(before, after, 1)


def patch_checkout(checkout: Path) -> None:
    if checkout == Path("/usr/share/omarchy") or Path("/usr/share/omarchy") in checkout.parents:
        raise ValueError("refusing to modify the installed Omarchy package")
    shell = checkout / "shell"
    bar_path = shell / "plugins/bar/Bar.qml"
    panel_path = shell / "Ui/KeyboardPanel.qml"
    qmldir_path = shell / "Ui/qmldir"
    launcher_paths = [shell / f"plugins/{name}/{file}.qml" for name, file in
                      (("menu", "Menu"), ("clipboard", "Clipboard"), ("emojis", "Emojis"))]
    notification_card_path = shell / "plugins/notifications/components/NotificationCard.qml"
    notification_service_path = shell / "plugins/notifications/Service.qml"
    osd_path = shell / "plugins/osd/Osd.qml"
    paths = (bar_path, panel_path, qmldir_path, notification_card_path,
             notification_service_path, osd_path, *launcher_paths)
    files = {path: path.read_text() for path in paths}

    bar = files[bar_path]
    bar = replace_once(bar, "  property var barConfig: ({})\n",
                       "  property var barConfig: ({})\n"
                       "  readonly property bool glassEnabled: barConfig.glassEnabled !== false\n", bar_path)
    bar = replace_once(bar,
        '    color: root.transparent ? "transparent" : root.background\n'
        '    surfaceFormat.opaque: false\n',
        '    color: root.glassEnabled ? "transparent" : (root.transparent ? "transparent" : root.background)\n'
        '    surfaceFormat.opaque: false\n'
        '    BackgroundEffect.blurRegion: root.glassEnabled ? barBlurRegion : null\n'
        '    Region { id: barBlurRegion; item: barWindow.contentItem }\n', bar_path)
    bar = replace_once(bar,
        '    HoverHandler { id: moduleHover }\n\n    BorderSurface {\n',
        '    HoverHandler { id: moduleHover }\n\n'
        '    GlassOverlay {\n'
        '      anchors.fill: parent\n'
        '      visible: root.glassEnabled && !!slot.activeItem && slot.activeItem.visible\n'
        '      radius: Math.min(Style.cornerRadius, height / 2)\n'
        '      reducedTransparency: root.barConfig.glassReducedTransparency === true\n'
        '      highContrast: root.barConfig.glassHighContrast === true\n'
        '      active: slot.hovered\n'
        '    }\n\n'
        '    BorderSurface {\n', bar_path)
    bar = replace_once(bar,
        '    onActiveItemChanged: Qt.callLater(injectProps)\n',
        '    GlassOverlay {\n'
        '      z: 40\n'
        '      anchors.fill: parent\n'
        '      visible: root.glassEnabled && !!slot.activeItem && slot.activeItem.visible\n'
        '      reflectionOnly: true\n'
        '      radius: Math.min(Style.cornerRadius, height / 2)\n'
        '      active: slot.hovered\n'
        '    }\n\n'
        '    onActiveItemChanged: Qt.callLater(injectProps)\n', bar_path)

    panel = files[panel_path]
    panel = replace_once(panel, '  property bool centerOnBar: false\n',
                         '  property bool centerOnBar: false\n'
                         '  readonly property bool glassEnabled: !!bar && "glassEnabled" in bar && bar.glassEnabled\n'
                         '  BackgroundEffect.blurRegion: glassEnabled ? cardBlurRegion : null\n'
                         '  Region { id: cardBlurRegion; item: card; radius: card.radius }\n', panel_path)
    panel = replace_once(panel,
        '    color: Color.popups.background\n'
        '    borderSpec: root.borderSpec\n',
        '    color: root.glassEnabled ? "transparent" : Color.popups.background\n'
        '    borderSpec: root.borderSpec\n', panel_path)
    panel = replace_once(panel,
        '    // Swallow clicks on the card so they don\'t bubble to the dismissal\n',
        '    GlassOverlay {\n'
        '      z: -1\n'
        '      anchors.fill: parent\n'
        '      visible: root.glassEnabled\n'
        '      radius: card.radius\n'
        '      reducedTransparency: !!root.bar && "barConfig" in root.bar && root.bar.barConfig.glassReducedTransparency === true\n'
        '      highContrast: !!root.bar && "barConfig" in root.bar && root.bar.barConfig.glassHighContrast === true\n'
        '    }\n\n'
        '    GlassOverlay {\n'
        '      z: 100\n'
        '      anchors.fill: parent\n'
        '      visible: root.glassEnabled\n'
        '      reflectionOnly: true\n'
        '      radius: card.radius\n'
        '    }\n\n'
        '    // Swallow clicks on the card so they don\'t bubble to the dismissal\n', panel_path)

    launchers = {}
    for path in launcher_paths:
        source = files[path]
        source = replace_once(source,
            '    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive\n',
            '    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive\n'
            '    BackgroundEffect.blurRegion: Region { item: card; radius: card.radius }\n',
            path)
        source = replace_once(source,
            '      color: root.background\n      borderSpec: root.borderSpec\n'
            '      padding: root.contentMargin\n\n      MouseArea { anchors.fill: parent; onClicked: {} }\n',
            '      color: "transparent"\n      borderSpec: root.borderSpec\n'
            '      padding: root.contentMargin\n\n'
            '      GlassOverlay { anchors.fill: parent; radius: card.radius }\n'
            '      GlassOverlay { z: 100; anchors.fill: parent; radius: card.radius; reflectionOnly: true }\n\n'
            '      MouseArea { anchors.fill: parent; onClicked: {} }\n', path)
        launchers[path] = source

    notification_card = files[notification_card_path]
    notification_card = replace_once(notification_card,
        '  property int cornerRadius: 0\n',
        '  property int cornerRadius: 0\n  property bool glassEnabled: false\n', notification_card_path)
    notification_card = replace_once(notification_card,
        '  color: Color.notifications.background\n  borderSpec: cardBorderSpec\n  clip: true\n',
        '  color: glassEnabled ? "transparent" : Color.notifications.background\n'
        '  borderSpec: cardBorderSpec\n  clip: true\n'
        '  GlassOverlay { anchors.fill: parent; radius: root.radius; visible: root.glassEnabled }\n'
        '  GlassOverlay { z: 100; anchors.fill: parent; radius: root.radius; visible: root.glassEnabled; reflectionOnly: true }\n',
        notification_card_path)
    notification_service = replace_once(files[notification_service_path],
        '      color: "transparent"\n\n      readonly property var popupPlacement:',
        '      color: "transparent"\n'
        '      BackgroundEffect.blurRegion: Region { item: popupColumn }\n\n'
        '      readonly property var popupPlacement:', notification_service_path)
    notification_service = replace_once(notification_service,
        '            NotificationCard {\n              id: card\n',
        '            NotificationCard {\n              id: card\n              glassEnabled: true\n',
        notification_service_path)

    osd = files[osd_path]
    osd = replace_once(osd,
        '    WlrLayershell.namespace: "omarchy-osd"\n',
        '    WlrLayershell.namespace: "omarchy-osd"\n'
        '    BackgroundEffect.blurRegion: Region { item: card; radius: card.radius }\n',
        osd_path)
    osd = replace_once(osd,
        '      color: Util.alpha(Color.background, 0.97)\n',
        '      color: "transparent"\n', osd_path)
    osd = replace_once(osd,
        '      opacity: root.opened ? 1 : 0\n\n      Row {\n',
        '      opacity: root.opened ? 1 : 0\n\n'
        '      GlassOverlay { anchors.fill: parent; radius: card.radius }\n'
        '      GlassOverlay { z: 100; anchors.fill: parent; radius: card.radius; reflectionOnly: true }\n\n'
        '      Row {\n', osd_path)

    qmldir = files[qmldir_path]
    if "GlassOverlay 1.0 GlassOverlay.qml\n" in qmldir:
        raise ValueError(f"already contains GlassOverlay: {qmldir_path}")
    qmldir += "GlassOverlay 1.0 GlassOverlay.qml\n"

    with tempfile.TemporaryDirectory() as temporary:
        compiled = Path(temporary) / "glass.frag.qsb"
        subprocess.run(["/usr/lib/qt6/bin/qsb", "--glsl", "100 es,120,150",
                        "--hlsl", "50", "--msl", "12", "-o", str(compiled),
                        str(PROJECT / "src/shaders/overlay.frag")], check=True)
        for path, content in ((bar_path, bar), (panel_path, panel), (qmldir_path, qmldir),
                              (notification_card_path, notification_card),
                              (notification_service_path, notification_service),
                              (osd_path, osd), *launchers.items()):
            path.write_text(content)
        shutil.copy2(PROJECT / "src/GlassOverlay.qml", shell / "Ui/GlassOverlay.qml")
        shader_dir = shell / "Ui/shaders"
        shader_dir.mkdir(exist_ok=True)
        shutil.copy2(compiled, shader_dir / "overlay.frag.qsb")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply.py /path/to/omarchy-source-checkout")
    patch_checkout(Path(sys.argv[1]).resolve())
