import QtQuick
import Quickshell

// Material painted above a compositor-provided backdrop. It never samples the
// screen: Hyprland supplies the blurred desktop behind this translucent layer,
// and GlassLens asks it to refract the desktop across the rim.
Item {
    id: root
    property real radius: 18
    property bool highContrast: false
    property bool reducedTransparency: false
    property bool active: false
    property bool reflectionOnly: false
    property real baseOpacity: 0.75
    property color tint: "#182330"
    property bool lens: !reflectionOnly && !reducedTransparency && !highContrast

    function lensRect() {
        const window = QsWindow.window as QsWindow
        if (!lens || !visible || !window || !window.visible) return null
        const rect = QsWindow.itemRect(root)
        let left = rect.x, top = rect.y, right = rect.x + rect.width, bottom = rect.y + rect.height
        for (let item = root; item; item = item.parent) {
            if (item.opacity < 0.5) return null
            // Rows scrolled out of a clipped list must not leak a lens.
            if (item !== root && item.clip) {
                const bounds = QsWindow.itemRect(item)
                left = Math.max(left, bounds.x)
                top = Math.max(top, bounds.y)
                right = Math.min(right, bounds.x + bounds.width)
                bottom = Math.min(bottom, bounds.y + bounds.height)
            }
        }
        if (right - left < 8 || bottom - top < 8) return null
        return {
            screen: window.screen ? window.screen.name : "",
            window: [QsWindow.contentItem.width, QsWindow.contentItem.height],
            rect: [left, top, right - left, bottom - top],
            radius: Math.max(0, Math.min(radius, (right - left) / 2, (bottom - top) / 2))
        }
    }

    onVisibleChanged: GlassLens.schedule()
    onLensChanged: GlassLens.schedule()
    Component.onCompleted: GlassLens.register(root)
    Component.onDestruction: GlassLens.unregister(root)

    Rectangle {
        anchors.fill: parent
        radius: root.radius
        color: Qt.rgba(root.tint.r, root.tint.g, root.tint.b, 1)
        visible: !root.reflectionOnly && GraphicsInfo.api === GraphicsInfo.Software
    }

    ShaderEffect {
        anchors.fill: parent
        visible: GraphicsInfo.api !== GraphicsInfo.Software
        property vector2d size: Qt.vector2d(width, height)
        property real radius: Math.max(0, Math.min(root.radius, width / 2, height / 2))
        property real opacityBase: root.reducedTransparency || root.highContrast ? 1.0 : root.baseOpacity
        property color tint: root.tint
        property real activity: root.active ? 1.0 : 0.0
        property real reflectionOnly: root.reflectionOnly ? 1.0 : 0.0
        fragmentShader: Qt.resolvedUrl("shaders/overlay.frag.qsb")
        onLogChanged: if (log) console.warn("GlassOverlay:", log)
    }
}
