import QtQuick

// Material painted above a compositor-provided backdrop. It never samples the
// screen: Hyprland supplies the blurred desktop behind this translucent layer.
Item {
    id: root
    property real radius: 18
    property bool highContrast: false
    property bool reducedTransparency: false
    property bool active: false
    property bool reflectionOnly: false
    property real baseOpacity: 0.16

    Rectangle {
        anchors.fill: parent
        radius: root.radius
        color: "#182330"
        visible: !root.reflectionOnly && GraphicsInfo.api === GraphicsInfo.Software
    }

    ShaderEffect {
        anchors.fill: parent
        visible: GraphicsInfo.api !== GraphicsInfo.Software
        property vector2d size: Qt.vector2d(width, height)
        property real radius: Math.max(0, Math.min(root.radius, width / 2, height / 2))
        property real opacityBase: root.reducedTransparency ? 0.92 : (root.highContrast ? 0.72 : root.baseOpacity)
        property real activity: root.active ? 1.0 : 0.0
        property real reflectionOnly: root.reflectionOnly ? 1.0 : 0.0
        fragmentShader: Qt.resolvedUrl("shaders/overlay.frag.qsb")
        onLogChanged: if (log) console.warn("GlassOverlay:", log)
    }
}
