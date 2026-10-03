pragma ComponentBehavior: Bound
import QtQuick
import ".."

Window {
    id: window
    width: 640
    height: 400
    visible: true
    property int phase: 0
    function assertColor(actual, expected, label) {
        const target = Qt.color(expected)
        if (Math.abs(actual.r - target.r) > 0.001 || Math.abs(actual.g - target.g) > 0.001
                || Math.abs(actual.b - target.b) > 0.001) {
            console.error("FAIL:", label, actual, "expected", expected)
            Qt.exit(1)
        }
    }
    Rectangle {
        id: preview
        anchors.fill: parent
        color: "#0b1020"
        property real refractionThickness: 0
        property real contentRefraction: 0
        property real ior: 1.5
        property bool glassEnabled: true
        property bool withSource: true
        property bool shared: false
        property bool showGlass: true
        property bool pressed: false
        property int backgroundMode: 0
        Item {
            id: backdrop
            anchors.fill: parent
            Repeater {
                model: preview.backgroundMode === 0 ? 40 : 0
                Rectangle {
                    required property int index
                    x: index * preview.width / 40
                    width: preview.width / 40
                    height: preview.height
                    color: index % 2 ? "#2c5590" : "#41867e"
                }
            }
            Rectangle {
                anchors.fill: parent
                visible: preview.backgroundMode !== 0
                color: preview.backgroundMode === 1 ? "white" : "#101010"
            }
            Text {
                anchors.centerIn: parent
                text: "Readable backdrop"
                color: preview.backgroundMode === 1 ? "black" : "white"
                font.pixelSize: 20
                style: Text.Sunken
                styleColor: "#50000000"
            }
        }
        ShaderEffectSource {
            id: sharedBackdrop
            visible: false
            sourceItem: backdrop
            sourceRect: Qt.rect(0, 0, preview.width, preview.height)
        }
        LiquidGlass {
            id: glass
            anchors.centerIn: parent
            width: 360
            height: 220
            sourceItem: preview.withSource ? backdrop : null
            thickness: preview.refractionThickness
            contentRefraction: preview.contentRefraction
            ior: preview.ior
            glassEnabled: preview.glassEnabled
            sharedSource: preview.shared ? sharedBackdrop : null
            visible: preview.showGlass
            interactive: false
            pressed: preview.pressed
            interaction: preview.pressed ? 1 : 0
            reducedMotion: true
        }
    }
    Timer {
        id: motionProbe
        interval: 70
        onTriggered: {
            if (!(glass.width > 360 && glass.width < 400)) {
                console.error("FAIL: geometry did not interpolate", glass.width)
                Qt.exit(1)
            }
        }
    }
    Loader {
        id: demo
        anchors.fill: parent
        active: false
        sourceComponent: Preview {}
        onLoaded: previewCapture.start()
    }
    Timer {
        id: previewCapture
        interval: 300
        onTriggered: {
            const previewItem = demo.item as Item
            previewItem.grabToImage(function(result) {
                Qt.exit(result.saveToFile("/tmp/widget-on-glass-preview.png") ? 0 : 1)
            })
        }
    }
    Timer {
        id: timer
        interval: 500
        running: true
        onTriggered: {
            if (window.phase === 0) {
                preview.contentRefraction = 2
                if (glass.safeContentRefraction !== 1) { console.error("FAIL: refraction upper clamp"); Qt.exit(1) }
                preview.contentRefraction = -1
                if (glass.safeContentRefraction !== 0) { console.error("FAIL: refraction lower clamp"); Qt.exit(1) }
                preview.contentRefraction = 0
                glass.backdropColor = "white"
                glass.highContrast = true
                window.assertColor(glass.contentColor, "white", "high-contrast fallback text")
                window.assertColor(glass.contentPlateColor, "#172334", "high-contrast fallback plate")
                glass.highContrast = false
                glass.reducedTransparency = true
                window.assertColor(glass.contentColor, "white", "reduced-transparency fallback text")
                glass.reducedTransparency = false
                preview.glassEnabled = false
                window.assertColor(glass.contentColor, "white", "disabled-glass fallback text")
                preview.glassEnabled = true
                preview.withSource = false
                window.assertColor(glass.contentColor, "white", "missing-source fallback text")
                preview.withSource = true
                glass.backdropColor = "#101010"
                window.assertColor(glass.contentColor, "white", "dark backdrop text")
                glass.backdropColor = "white"
                window.assertColor(glass.contentColor, "#172334", "light backdrop text")
                glass.backdropColor = "transparent"
            }
            if (preview.GraphicsInfo.api === GraphicsInfo.Software) {
                console.error("FAIL: software scenegraph cannot validate ShaderEffect")
                Qt.exit(1)
                return
            }
            preview.grabToImage(function(result) {
                if (!result.saveToFile("/tmp/widget-on-glass-render-" + window.phase + ".png")) {
                    Qt.exit(1)
                    return
                }
                window.phase += 1
                if (window.phase === 1) {
                    preview.refractionThickness = 80
                } else if (window.phase === 2) {
                    preview.ior = 1
                    preview.refractionThickness = 0
                } else if (window.phase === 3) {
                    preview.refractionThickness = 80
                } else if (window.phase === 4) {
                    preview.glassEnabled = false
                } else if (window.phase === 5) {
                    preview.glassEnabled = true
                    preview.withSource = false
                } else if (window.phase === 6) {
                    preview.showGlass = false
                } else if (window.phase === 7) {
                    preview.showGlass = true
                    preview.withSource = true
                    preview.shared = true
                    preview.ior = 1.5
                } else if (window.phase === 8) {
                    preview.pressed = true
                } else if (window.phase === 9) {
                    preview.pressed = false
                    preview.backgroundMode = 1
                } else if (window.phase === 10) {
                    preview.backgroundMode = 2
                } else if (window.phase === 11) {
                    preview.showGlass = false
                } else if (window.phase === 12) {
                    preview.backgroundMode = 1
                } else if (window.phase === 13) {
                    preview.showGlass = true
                    glass.reducedMotion = false
                    glass.width = 400
                    motionProbe.start()
                } else if (window.phase === 14) {
                    if (glass.width !== 400) { Qt.exit(1); return }
                    glass.reducedMotion = true
                    glass.width = 360
                    if (glass.width !== 360) { Qt.exit(1); return }
                    preview.refractionThickness = 36
                    preview.backgroundMode = 2
                    preview.contentRefraction = 0.45
                } else if (window.phase === 15) {
                    preview.contentRefraction = 0
                } else if (window.phase === 16) {
                    preview.backgroundMode = 1
                    preview.contentRefraction = 0.45
                } else if (window.phase === 17) {
                    preview.contentRefraction = 0
                } else {
                    console.log("Refraction, content parallax, neutral IOR, fallback, shared source, interaction and readability renders saved; API:", preview.GraphicsInfo.api)
                    console.log("PASS: geometry interpolates; reduced motion changes geometry immediately")
                    preview.visible = false
                    demo.active = true
                    return
                }
                timer.restart()
            })
        }
    }
}
