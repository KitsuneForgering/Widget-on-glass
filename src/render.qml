pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import "."

ShellRoot {
FloatingWindow {
    id: window
    implicitWidth: 640
    implicitHeight: 360
    visible: true

    Item {
        id: scene
        anchors.fill: parent
        Item {
            id: backdrop
            anchors.fill: parent
            Rectangle { anchors.fill: parent; color: "#1d314e" }
            Repeater {
                model: 32
                Rectangle {
                    required property int index
                    x: index * 20
                    width: 10
                    height: scene.height
                    color: index % 2 ? "#66a2ae" : "#a4c58c"
                }
            }
        }
        ShaderEffectSource {
            id: texture
            sourceItem: backdrop
            sourceRect: Qt.rect(0, 0, backdrop.width, backdrop.height)
            visible: false
        }
        GlassWidget {
            id: glass
            x: 80; y: 70; width: 480; height: 220
            sourceItem: backdrop
            sourceTexture: texture
            thickness: 0
            radius: 28
        }
    }

    Timer {
        interval: 500
        running: true
        onTriggered: {
            if (scene.GraphicsInfo.api === GraphicsInfo.Software) {
                console.error("FAIL: software backend cannot test ShaderEffect")
                Qt.exit(1)
                return
            }
            scene.grabToImage(function(result) {
                if (!result.saveToFile("/tmp/widget-on-glass-pilot-0.png")) {
                    Qt.exit(1)
                    return
                }
                glass.thickness = 60
                capture.restart()
            })
        }
    }
    Timer {
        id: capture
        interval: 500
        onTriggered: {
            scene.grabToImage(function(result) {
                if (!result.saveToFile("/tmp/widget-on-glass-pilot-1.png")) Qt.exit(1)
                else {
                    console.log("PASS: GPU frames captured; API", scene.GraphicsInfo.api)
                    Qt.exit(0)
                }
            })
        }
    }
}
}
