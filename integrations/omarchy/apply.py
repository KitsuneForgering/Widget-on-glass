"""Apply the compositor-backed glass pilot to an Omarchy source checkout.

Usage: python3 integrations/omarchy/apply.py /path/to/omarchy
The checkout must match the shell layout inspected on 2026-10-03.
"""

from pathlib import Path
import re
import shutil
import subprocess
import sys


PROJECT = Path(__file__).resolve().parents[2]


def replace_once(source: str, before: str, after: str, path: Path) -> str:
    if source.count(before) != 1:
        raise ValueError(f"expected one anchor in {path}: {before[:70]!r}")
    return source.replace(before, after, 1)


def patch_tray(checkout: Path) -> None:
    tray_path = checkout / "shell/plugins/bar/widgets/Tray.qml"
    source = tray_path.read_text()
    if "root.allItems.length > 0 ? expandIcon.implicitWidth + root.revealExtent : 0" not in source:
        for before, after in (
          ("root.allItems.length > 0 ? expandIcon.implicitWidth + root.drawerExtent : 0",
           "root.allItems.length > 0 ? expandIcon.implicitWidth + root.revealExtent : 0"),
          ("root.allItems.length > 0 ? expandIcon.implicitHeight + root.drawerExtent : 0",
           "root.allItems.length > 0 ? expandIcon.implicitHeight + root.revealExtent : 0"),
          ("var chevronX = root.drawerExtent - root.revealExtent", "var chevronX = 0"),
          ("var chevronY = root.drawerExtent - root.revealExtent", "var chevronY = 0"),
          ("width: root.drawerExtent\n          height: root.barSize",
           "width: root.revealExtent\n          height: root.barSize"),
          ("width: root.barSize\n          height: root.drawerExtent",
           "width: root.barSize\n          height: root.revealExtent"),
          ("          x: root.drawerExtent - root.revealExtent\n          text: \"\\uf053\"",
           "          x: 0\n          text: \"\\uf053\""),
          ("          y: root.drawerExtent - root.revealExtent\n          text: \"\\uf053\"",
           "          y: 0\n          text: \"\\uf053\""),
          ("            x: root.drawerExtent - root.revealExtent\n            anchors.verticalCenter",
           "            x: root.revealExtent - root.drawerExtent\n            anchors.verticalCenter"),
          ("            y: root.drawerExtent - root.revealExtent\n            anchors.horizontalCenter",
           "            y: root.revealExtent - root.drawerExtent\n            anchors.horizontalCenter"),
        ):
            source = replace_once(source, before, after, tray_path)
            tray_path.write_text(source)


def remove_menu_lens(checkout: Path) -> None:
    """Drop the menu-only lens of earlier versions; GlassLens now covers every surface."""
    path = checkout / "shell/plugins/menu/Menu.qml"
    source = path.read_text()
    restored = re.sub(r"(?s)(  PanelWindow \{\n    id: panel\n)    Timer \{\n      id: lensTimer\n.*?"
                      r"      function onHeightChanged\(\) \{ if \(root.opened\) lensTimer.restart\(\) \}\n    \}\n",
                      r"\1", source, count=1)
    if "widget-on-glass-menu-lens" in restored:
        raise ValueError(f"could not remove the old menu lens: {path}")
    if restored != source:
        path.write_text(restored)
    (checkout / "bin/widget-on-glass-menu-lens").unlink(missing_ok=True)


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

    for path, content in ((bar_path, bar), (panel_path, panel), (qmldir_path, qmldir),
                          (notification_card_path, notification_card),
                          (notification_service_path, notification_service),
                          (osd_path, osd), *launchers.items()):
        path.write_text(content)
    refresh(checkout)


def remove_appearance(checkout: Path) -> None:
    shell = checkout / "shell"
    paths = [shell / "plugins/bar/Bar.qml", shell / "Ui/KeyboardPanel.qml",
             shell / "plugins/notifications/components/NotificationCard.qml",
             *(shell / f"plugins/{name}/{file}.qml" for name, file in
               (("osd", "Osd"), ("menu", "Menu"), ("clipboard", "Clipboard"), ("emojis", "Emojis")))]
    for path in paths:
        source = path.read_text()
        restored = re.sub(r"(?m)^([ \t]*)layer.enabled: [^\n]*\n\1layer.effect: GlassAppearance \{[^\n]*\}\n",
                          "", source)
        if restored != source:
            path.write_text(restored)
    qmldir = shell / "Ui/qmldir"
    source = qmldir.read_text()
    restored = source.replace("GlassAppearance 1.0 GlassAppearance.qml\n", "").replace(
        "singleton GlassBackdrop 1.0 GlassBackdrop.qml\n", "")
    if restored != source:
        qmldir.write_text(restored)
    for name in ("GlassAppearance.qml", "GlassBackdrop.qml"):
        (shell / "Ui" / name).unlink(missing_ok=True)


# Launchers sit over a veil with a hole, so they can be clearer than panels; their
# secondary text is fully opaque to keep 4.5:1 at this opacity.
LAUNCHER_GLASS = "GlassOverlay { anchors.fill: parent; radius: card.radius; tint: root.background; baseOpacity: 0.75 }"


def patch_tints(checkout: Path) -> None:
    shell = checkout / "shell"
    changes = {
        shell / "plugins/bar/Bar.qml": (
            "GlassOverlay {\n      anchors.fill: parent\n      visible: root.glassEnabled",
            "GlassOverlay {\n      anchors.fill: parent\n      tint: root.background\n      baseOpacity: 0.75\n      visible: root.glassEnabled"),
        shell / "Ui/KeyboardPanel.qml": (
            "GlassOverlay {\n      z: -1\n      anchors.fill: parent",
            "GlassOverlay {\n      z: -1\n      anchors.fill: parent\n      tint: Color.popups.background"),
        shell / "plugins/notifications/components/NotificationCard.qml": (
            "GlassOverlay { anchors.fill: parent; radius: root.radius; visible: root.glassEnabled }",
            "GlassOverlay { anchors.fill: parent; radius: root.radius; tint: Color.notifications.background; visible: root.glassEnabled }"),
        shell / "plugins/osd/Osd.qml": (
            "GlassOverlay { anchors.fill: parent; radius: card.radius }",
            "GlassOverlay { anchors.fill: parent; radius: card.radius; tint: Color.popups.background }"),
        **{shell / f"plugins/{name}/{file}.qml": (
            "GlassOverlay { anchors.fill: parent; radius: card.radius }",
            LAUNCHER_GLASS)
           for name, file in (("menu", "Menu"), ("clipboard", "Clipboard"), ("emojis", "Emojis"))},
    }
    for path, (before, after) in changes.items():
        source = path.read_text()
        if path.name == "Bar.qml":
            source = source.replace("      baseOpacity: 0.80\n", "      baseOpacity: 0.75\n")
        # Launchers of earlier versions used the panels' opacity.
        source = source.replace("GlassOverlay { anchors.fill: parent; radius: card.radius; tint: root.background }",
                                LAUNCHER_GLASS)
        if after not in source:
            source = replace_once(source, before, after, path)
        path.write_text(source)


def patch_secondary_text(checkout: Path) -> None:
    for name in ("menu", "clipboard"):
        path = checkout / f"shell/plugins/{name}/{name.capitalize()}.qml"
        source = path.read_text()
        changes = [("opacity: root.filterText ? 1 : 0.58",
                    "opacity: root.filterText ? 1 : 0.72")]
        if name == "menu":
            source = source.replace("opacity: 0.86\n", "opacity: 1\n", 1)
            changes += [("opacity: 0.52", "opacity: 1"),
                        ('opacity: row.kind === "menu" || row.kind === "link" ? 0.36 : 0',
                         'opacity: row.kind === "menu" || row.kind === "link" ? 0.60 : 0')]
        else:
            source = source.replace('entryType === "file" ? 0.86 : 1.0', 'entryType === "file" ? 1.0 : 1.0')
            changes.append(('opacity: parent.parent.entryType === "image" || parent.parent.entryType === "file" ? 0.72 : 1.0',
                            'opacity: parent.parent.entryType === "image" || parent.parent.entryType === "file" ? 1.0 : 1.0'))
        for before, after in changes:
            if after not in source:
                source = replace_once(source, before, after, path)
        path.write_text(source)


def patch_popup_card(checkout: Path) -> None:
    path = checkout / "shell/Ui/PopupCard.qml"
    source = path.read_text()
    if "import Quickshell.Wayland\n" not in source:
        source = replace_once(source, "import Quickshell.Hyprland\n",
                              "import Quickshell.Hyprland\nimport Quickshell.Wayland\n", path)
    if "BackgroundEffect.blurRegion: Region { item: card; radius: card.radius }" not in source:
        source = replace_once(source, '  color: "transparent"\n  implicitWidth: contentWidth\n',
                              '  color: "transparent"\n'
                              '  BackgroundEffect.blurRegion: Region { item: card; radius: card.radius }\n'
                              '  implicitWidth: contentWidth\n', path)
    if 'GlassOverlay { anchors.fill: parent; radius: card.radius; tint: Color.popups.background }' not in source:
        source = replace_once(source, '    color: Color.popups.background\n    borderSpec: root.borderSpec\n',
                              '    color: "transparent"\n    borderSpec: root.borderSpec\n', path)
        source = replace_once(source, '    Item {\n      id: contentHolder\n',
                              '    GlassOverlay { anchors.fill: parent; radius: card.radius; tint: Color.popups.background }\n'
                              '    GlassOverlay { z: 100; anchors.fill: parent; radius: card.radius; reflectionOnly: true }\n\n'
                              '    Item {\n      id: contentHolder\n', path)
    path.write_text(source)


def patch_local_plugins() -> None:
    path = Path.home() / ".config/omarchy/plugins/tornikegomareli.spaces/Spaces.qml"
    if not path.exists():
        return
    source = path.read_text()
    before = "      color: Qt.rgba(root.bg.r, root.bg.g, root.bg.b, 0.97)\n"
    after = '      color: "transparent"\n'
    old_comment = "    // Popups get no compositor blur, so the card needs its own opaque fill.\n"
    new_comment = "    // PopupCard supplies the glass background.\n"
    if before in source:
        backup = path.with_name("Spaces.qml.widget-on-glass.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
        source = replace_once(source, before, after, path)
    elif after not in source:
        raise ValueError(f"Spaces preview changed unexpectedly: {path}")
    if old_comment in source:
        source = replace_once(source, old_comment, new_comment, path)
    path.write_text(source)


def patch_inner_glass(checkout: Path) -> None:
    """Carry the glass into the surfaces drawn inside the integrated cards."""
    shell = checkout / "shell"

    def edit(path: Path, changes) -> None:
        source = path.read_text()
        for before, after in changes:
            if after not in source:
                source = replace_once(source, before, after, path)
        path.write_text(source)

    # Filled rows, buttons and chips inside panels are BorderSurfaces.
    edit(shell / "Ui/BorderSurface.qml", [(
        "  Loader {\n    anchors.fill: parent\n    active: root.usesOverlayBorder\n",
        "  // Widget on Glass: a filled inner surface gets the glass rim and lens.\n"
        "  Loader {\n    z: 100\n    anchors.fill: parent\n"
        "    active: root.color.a > 0.01 && root.width >= 8 && root.height >= 8\n"
        "    sourceComponent: GlassOverlay { radius: root.radius; reflectionOnly: true; lens: true }\n  }\n\n"
        "  Loader {\n    anchors.fill: parent\n    active: root.usesOverlayBorder\n")])

    # The veil used to cover the card too, darkening the glass under it.
    scrim = ("    Rectangle {\n      anchors.fill: parent\n      color: root.scrim\n    }\n",
             "    GlassScrim { color: root.scrim; hole: card }\n")
    edit(shell / "plugins/menu/Menu.qml", [scrim])
    edit(shell / "plugins/clipboard/Clipboard.qml", [scrim, (
        '                  color: hasCursor ? root.selectedBackground : "transparent"\n',
        '                  color: hasCursor ? root.selectedBackground : "transparent"\n'
        '                  GlassOverlay { z: 50; anchors.fill: parent; radius: row.radius; visible: row.hasCursor; reflectionOnly: true; lens: true }\n')])
    edit(shell / "plugins/emojis/Emojis.qml", [scrim, (
        '              color: hasCursor ? root.selectedBackground : "transparent"\n',
        '              color: hasCursor ? root.selectedBackground : "transparent"\n'
        '              GlassOverlay { z: 50; anchors.fill: parent; radius: parent.radius; visible: parent.hasCursor; reflectionOnly: true; lens: true }\n')])

    popup_glass = ("        background: BorderSurface {\n          color: root.background\n"
                   "          borderSpec: root.popupBorderSpec\n          radius: Style.cornerRadius\n        }\n",
                   "        background: BorderSurface {\n          id: popupSurface\n          color: \"transparent\"\n"
                   "          borderSpec: root.popupBorderSpec\n          radius: Style.cornerRadius\n"
                   "          GlassOverlay { anchors.fill: parent; radius: popupSurface.radius; tint: root.background }\n"
                   "          GlassOverlay { z: 100; anchors.fill: parent; radius: popupSurface.radius; reflectionOnly: true }\n"
                   "        }\n")
    for name, view in (("Dropdown", "optionList"), ("SearchableDropdown", "resultList"), ("MultiSelect", "resultList")):
        path = shell / f"Ui/{name}.qml"
        source = path.read_text()
        if "GlassOverlay" not in source:
            source = replace_once(source, *popup_glass, path)
            highlight = re.compile(r"(?m)^(?P<i>[ ]+)color: index === " + view + r"\.currentIndex\n"
                                   r"(?P=i)  \? Style\.hoverFillFor\(root\.foreground, root\.accent\)\n"
                                   r"(?P=i)  : \"transparent\"\n")
            source, count = highlight.subn(
                lambda m: m.group(0) + m.group("i") + "GlassOverlay { z: 50; anchors.fill: parent; visible: index === "
                + view + ".currentIndex; radius: 0; reflectionOnly: true; lens: true }\n", source)
            if count != 1:
                raise ValueError(f"unexpected highlight in {path}")
            path.write_text(source)

    edit(shell / "Ui/ConfirmDialog.qml", [(
        "      color: root.background\n      borderSpec: Border.flat(root.selectedText, Style.normalBorderWidth)\n"
        "      padding: Style.space(18)\n      radius: root.cornerRadius\n",
        "      color: \"transparent\"\n      borderSpec: Border.flat(root.selectedText, Style.normalBorderWidth)\n"
        "      padding: Style.space(18)\n      radius: root.cornerRadius\n\n"
        "      GlassOverlay { anchors.fill: parent; radius: card.radius; tint: root.background }\n"
        "      GlassOverlay { z: 100; anchors.fill: parent; radius: card.radius; reflectionOnly: true }\n")])


def refresh(checkout: Path) -> None:
    """Refresh a patched checkout without changing the widgets' content."""
    if checkout == Path("/usr/share/omarchy") or Path("/usr/share/omarchy") in checkout.parents:
        raise ValueError("refusing to modify the installed Omarchy package")
    shader_dir = checkout / "shell/Ui/shaders"
    shader_dir.mkdir(exist_ok=True)
    subprocess.run(["/usr/lib/qt6/bin/qsb", "--glsl", "100 es,120,150",
                    "--hlsl", "50", "--msl", "12", "-o", str(shader_dir / "overlay.frag.qsb"),
                    str(PROJECT / "src/shaders/overlay.frag")], check=True)
    shutil.copy2(PROJECT / "src/GlassOverlay.qml", checkout / "shell/Ui/GlassOverlay.qml")
    for name in ("GlassLens.qml", "GlassScrim.qml"):
        shutil.copy2(PROJECT / "src" / name, checkout / "shell/Ui" / name)
    lens = checkout / "bin/widget-on-glass-lens"
    shutil.copy2(PROJECT / "integrations/omarchy/lens.py", lens)
    lens.chmod(0o755)
    qmldir = checkout / "shell/Ui/qmldir"
    source = qmldir.read_text()
    for line in ("singleton GlassLens 1.0 GlassLens.qml\n", "GlassScrim 1.0 GlassScrim.qml\n"):
        if line not in source:
            source += line
    qmldir.write_text(source)
    remove_menu_lens(checkout)
    remove_appearance(checkout)
    patch_tints(checkout)
    patch_secondary_text(checkout)
    patch_popup_card(checkout)
    patch_tray(checkout)
    patch_inner_glass(checkout)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--local-plugins":
        patch_local_plugins()
    elif len(sys.argv) == 3 and sys.argv[1] == "--refresh":
        refresh(Path(sys.argv[2]).resolve())
    elif len(sys.argv) == 2:
        patch_checkout(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("usage: apply.py [--refresh] /path/to/omarchy-source-checkout | --local-plugins")
