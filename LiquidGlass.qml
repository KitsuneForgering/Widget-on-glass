pragma ComponentBehavior: Bound
import QtQuick

Item {
    id: root
    // Source must be a separate, untransformed sibling, never an ancestor containing this item.
    property Item sourceItem: null
    property bool glassEnabled: true
    property bool reducedTransparency: false
    property bool highContrast: false
    property bool reducedMotion: false
    property bool interactive: true
    property bool pressed: false
    property bool activeSurface: true
    property bool preserveBackground: true
    property ShaderEffectSource sharedSource: null
    // Supply a representative color from the readable area under this glass.
    // Qt Quick shaders cannot return sampled pixels to QML without GPU readback.
    property color backdropColor: "transparent"
    property real radius: 24
    property real bevel: 24
    property real thickness: 36
    property real contentRefraction: 0
    property real ior: 1.5
    property color tint: Qt.rgba(0.04, 0.06, 0.10, 0.12)
    property real interaction: interactive ? (pressed ? 1 : hover.hovered ? 0.45 : 0) : 0
    default property alias content: foreground.data
    readonly property color fallbackColor: highContrast ? "black" : "#111827"
    readonly property color effectiveBackdropColor: refracting && backdropColor.a > 0
        ? backdropColor : fallbackColor
    readonly property real backdropLuminance: 0.2126 * linearChannel(effectiveBackdropColor.r)
        + 0.7152 * linearChannel(effectiveBackdropColor.g)
        + 0.0722 * linearChannel(effectiveBackdropColor.b)
    // These opaque pairs exceed WCAG AAA's 7:1 text contrast requirement.
    readonly property color contentColor: backdropLuminance > 0.179 ? "#172334" : "#ffffff"
    readonly property color contentPlateColor: backdropLuminance > 0.179 ? "#f5f7fa" : "#172334"

    function linearChannel(channel) {
        return channel <= 0.04045 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4)
    }
    readonly property bool refracting: glassEnabled && !reducedTransparency && !highContrast && sourceItem !== null
        && (!sharedSource || sharedSource.sourceItem === sourceItem)
        && textureRegion.width > 0 && textureRegion.height > 0
        && GraphicsInfo.api !== GraphicsInfo.Software
    readonly property real safeRadius: Math.max(0, Math.min(radius, width / 2, height / 2))
    readonly property real safeThickness: Math.max(0, Math.min(thickness, 128))
    readonly property real safeContentRefraction: Math.max(0, Math.min(contentRefraction, 1))
    // Fixed crop: changing thickness must not change texture rasterization.
    readonly property real padding: 130
    readonly property point sourcePosition: sourceItem
        ? Qt.point(x - sourceItem.x, y - sourceItem.y) : Qt.point(0, 0)
    readonly property rect textureRegion: sharedSource
        ? (sharedSource.sourceRect.width > 0 && sharedSource.sourceRect.height > 0
            ? sharedSource.sourceRect : Qt.rect(0, 0, sourceItem ? sourceItem.width : 0, sourceItem ? sourceItem.height : 0))
        : Qt.rect(sourcePosition.x - padding, sourcePosition.y - padding,
                  width + 2 * padding, height + 2 * padding)

    HoverHandler { id: hover; enabled: root.interactive && root.enabled; blocking: false }
    Behavior on interaction { NumberAnimation { duration: root.reducedMotion ? 0 : 120 } }
    Behavior on width { enabled: !root.reducedMotion; NumberAnimation { duration: 180; easing.type: Easing.InOutCubic } }
    Behavior on height { enabled: !root.reducedMotion; NumberAnimation { duration: 180; easing.type: Easing.InOutCubic } }
    Behavior on radius { enabled: !root.reducedMotion; NumberAnimation { duration: 180; easing.type: Easing.InOutCubic } }

    Rectangle {
        anchors.fill: parent
        visible: !root.refracting
        radius: root.safeRadius
        color: root.fallbackColor
        border.color: root.highContrast ? "white" : "#536176"
    }

    Loader {
        anchors.fill: parent
        active: root.refracting && root.visible && root.width > 0 && root.height > 0
            && root.textureRegion.width > 0 && root.textureRegion.height > 0
        sourceComponent: ShaderEffect {
            property var source: root.sharedSource || backdropTexture
            property vector2d size: Qt.vector2d(width, height)
            property real radius: root.safeRadius
            property real bevel: Math.max(1, root.bevel)
            property real thickness: root.safeThickness
            property real contentRefraction: root.safeContentRefraction
            property real ior: Math.max(1, Math.min(root.ior, 2.5))
            property vector2d sourceExtent: Qt.vector2d(root.textureRegion.width, root.textureRegion.height)
            property vector4d sampleRect: Qt.vector4d(
                (root.sourcePosition.x - root.textureRegion.x) / Math.max(1, root.textureRegion.width),
                (root.sourcePosition.y - root.textureRegion.y) / Math.max(1, root.textureRegion.height),
                root.width / Math.max(1, root.textureRegion.width),
                root.height / Math.max(1, root.textureRegion.height))
            property real interaction: root.interaction
            property real activeSurface: root.activeSurface ? 1 : 0.35
            property real preserveBackground: root.preserveBackground ? 1 : 0
            property vector4d tint: Qt.vector4d(root.tint.r, root.tint.g, root.tint.b, root.tint.a)
            fragmentShader: Qt.resolvedUrl("shaders/glass.frag.qsb")
            onLogChanged: if (log) console.warn("LiquidGlass:", log)

            ShaderEffectSource {
                id: backdropTexture
                visible: false
                sourceItem: root.sharedSource ? null : root.sourceItem
                sourceRect: root.textureRegion
                live: true
                // Local crop only when no shared sampling region is provided.
            }
        }
    }

    Item { id: foreground; anchors.fill: parent }
}
