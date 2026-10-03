pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

// Collects the visible GlassOverlay rectangles and hands them to the compositor
// helper, which turns them into one Hyprland screen_shader rim lens.
Singleton {
    id: root

    // Only the linked Omarchy shell drives the compositor; demos never do.
    readonly property bool enabled: Quickshell.env("OMARCHY_PATH") !== null
        && Quickshell.shellDir === Quickshell.env("OMARCHY_PATH") + "/shell"
    readonly property string helper: Quickshell.env("OMARCHY_PATH") + "/bin/widget-on-glass-lens"
    property var overlays: []
    property string sent: ""
    property bool dirty: false

    function register(overlay) {
        if (overlays.indexOf(overlay) < 0) overlays = overlays.concat([overlay])
        schedule()
    }

    function unregister(overlay) {
        overlays = overlays.filter(o => o !== overlay)
        schedule()
    }

    function schedule() {
        if (enabled) debounce.restart()
    }

    function snapshot() {
        const rects = []
        for (const overlay of overlays) {
            const rect = overlay.lensRect()
            if (rect) rects.push(rect)
        }
        const fullscreen = Hyprland.monitors.values
            .filter(m => m.activeWorkspace && m.activeWorkspace.hasFullscreen)
            .map(m => m.name)
        return JSON.stringify({ rects: rects, fullscreen: fullscreen })
    }

    function update() {
        const state = snapshot()
        if (state === sent) return
        if (proc.running) { dirty = true; return }
        sent = state
        proc.command = [helper, "apply", state]
        proc.running = true
    }

    Timer { id: debounce; interval: 60; onTriggered: root.update() }
    // Parents move and animate without telling their children; polling the
    // few registered rectangles is cheaper than wiring every ancestor.
    Timer { interval: 300; repeat: true; running: root.enabled; onTriggered: root.update() }

    Process {
        id: proc
        onRunningChanged: if (!running && root.dirty) { root.dirty = false; root.update() }
    }

    Connections {
        target: Hyprland
        enabled: root.enabled
        // A config reload resets screen_shader; resend the current lens.
        function onRawEvent(event) {
            if (event.name === "configreloaded") { root.sent = ""; root.schedule() }
        }
    }

    // The helper reads the glass switches from shell.json; resend when it changes.
    FileView {
        path: Quickshell.env("HOME") + "/.config/omarchy/shell.json"
        watchChanges: root.enabled
        onFileChanged: { root.sent = ""; root.schedule() }
    }

    Component.onDestruction: if (enabled) Quickshell.execDetached([helper, "clear"])
}
