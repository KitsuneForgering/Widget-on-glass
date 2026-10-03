pragma ComponentBehavior: Bound
import QtQuick
import Quickshell

Item {
    id: root
    // The texture covers sourceItem in full and belongs to the same QQuickWindow.
    property Item sourceItem: null
    property ShaderEffectSource sourceTexture: null
    property bool glassEnabled: true
    property bool reducedTransparency: false
    property bool highContrast: false
    property bool reducedMotion: false
    property real radius: 18
    property real bevel: 20
    property real thickness: 24
    property real ior: 1.5
    property color fallbackColor: highContrast ? "black" : "#172334"
    default property alias content: foreground.data

    readonly property bool refracting: glassEnabled && !reducedTransparency && !highContrast
        && sourceItem !== null && sourceTexture !== null
        && sourceTexture.sourceItem === sourceItem && sourceItem.width > 0 && sourceItem.height > 0
        && GraphicsInfo.api !== GraphicsInfo.Software
    readonly property real safeRadius: Math.max(0, Math.min(radius, width / 2, height / 2))
    readonly property real safeThickness: Math.max(0, Math.min(thickness, 96))
    readonly property point sourcePosition: {
        sourceTransform.transform
        return sourceItem ? root.mapToItem(sourceItem, 0, 0) : Qt.point(0, 0)
    }

    TransformWatcher { id: sourceTransform; a: root.sourceItem; b: root }

    HoverHandler { id: hover; blocking: false }

    Rectangle {
        anchors.fill: parent
        radius: root.safeRadius
        color: root.fallbackColor
        border.color: root.highContrast ? "white" : "#73839c"
        visible: !root.refracting
    }

    ShaderEffect {
        anchors.fill: parent
        visible: root.refracting
        property var source: root.sourceTexture
        property vector2d size: Qt.vector2d(width, height)
        property vector2d sourceSize: Qt.vector2d(root.sourceItem ? root.sourceItem.width : 1,
                                                   root.sourceItem ? root.sourceItem.height : 1)
        property vector4d sampleRect: Qt.vector4d(
            root.sourcePosition.x / Math.max(1, root.sourceItem ? root.sourceItem.width : 1),
            root.sourcePosition.y / Math.max(1, root.sourceItem ? root.sourceItem.height : 1),
            root.width / Math.max(1, root.sourceItem ? root.sourceItem.width : 1),
            root.height / Math.max(1, root.sourceItem ? root.sourceItem.height : 1))
        property real radius: root.safeRadius
        property real bevel: Math.max(1, root.bevel)
        property real thickness: root.safeThickness
        property real ior: Math.max(1, Math.min(root.ior, 2.5))
        property real interaction: root.reducedMotion ? 0 : (hover.hovered ? 1 : 0)
        fragmentShader: Qt.resolvedUrl("shaders/glass.frag.qsb")
        onLogChanged: if (log) console.warn("GlassWidget:", log)
    }

    Item { id: foreground; anchors.fill: parent }
}
