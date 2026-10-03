pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland
import "."

ShellRoot {
    id: shell
    property bool panelOpen: false

    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: bar
            property var modelData
            screen: modelData
            implicitHeight: 68
            exclusionMode: ExclusionMode.Ignore
            anchors { top: true; left: true; right: true }
            color: "transparent"
            surfaceFormat.opaque: false
            WlrLayershell.namespace: "widget-on-glass-bar"
            WlrLayershell.layer: WlrLayer.Top

            Item {
                id: barScene
                anchors.fill: parent
                Item {
                    id: barBackdrop
                    anchors.fill: parent
                    Rectangle {
                        anchors.fill: parent
                        color: "#12213b"
                        gradient: Gradient {
                            GradientStop { position: 0; color: "#204c63" }
                            GradientStop { position: 1; color: "#273251" }
                        }
                    }
                    Rectangle { x: bar.width * 0.35; width: 80; height: parent.height; color: "#476e92"; opacity: 0.45 }
                }
                ShaderEffectSource {
                    id: barTexture
                    sourceItem: barBackdrop
                    sourceRect: Qt.rect(0, 0, barBackdrop.width, barBackdrop.height)
                    visible: false
                    live: true
                }
                GlassWidget {
                    id: titleGlass
                    sourceItem: barBackdrop
                    sourceTexture: barTexture
                    x: 12; y: 10; width: 196; height: 48
                    Text { anchors.centerIn: parent; text: "Widget on Glass"; color: "white"; font.bold: true }
                }
                GlassWidget {
                    id: actionGlass
                    sourceItem: barBackdrop
                    sourceTexture: barTexture
                    x: bar.width - width - 12; y: 10; width: 112; height: 48
                    Text { anchors.centerIn: parent; text: shell.panelOpen ? "Fechar" : "Abrir"; color: "white" }
                    TapHandler { onTapped: shell.panelOpen = !shell.panelOpen }
                }
            }
        }
    }

    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: panel
            property var modelData
            screen: modelData
            visible: shell.panelOpen
            implicitWidth: 380
            implicitHeight: 260
            anchors { top: true; right: true }
            margins { top: 80; right: 12 }
            exclusionMode: ExclusionMode.Ignore
            color: "transparent"
            surfaceFormat.opaque: false
            WlrLayershell.namespace: "widget-on-glass-panel"
            WlrLayershell.layer: WlrLayer.Overlay

            Item {
                anchors.fill: parent
                Item {
                    id: panelBackdrop
                    anchors.fill: parent
                    Rectangle {
                        anchors.fill: parent
                        gradient: Gradient {
                            GradientStop { position: 0; color: "#2b5d78" }
                            GradientStop { position: 1; color: "#15253c" }
                        }
                    }
                    Rectangle { x: 260; y: 40; width: 80; height: 180; radius: 40; color: "#6193b8"; opacity: 0.4 }
                }
                ShaderEffectSource {
                    id: panelTexture
                    sourceItem: panelBackdrop
                    sourceRect: Qt.rect(0, 0, panelBackdrop.width, panelBackdrop.height)
                    visible: false
                    live: panel.visible
                }
                GlassWidget {
                    sourceItem: panelBackdrop
                    sourceTexture: panelTexture
                    x: 16; y: 16; width: 348; height: 100
                    Text { anchors.centerIn: parent; text: "Painel Quickshell"; color: "white"; font.pixelSize: 22 }
                }
                GlassWidget {
                    sourceItem: panelBackdrop
                    sourceTexture: panelTexture
                    x: 16; y: 130; width: 348; height: 104
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 30
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        text: "Uma textura GPU compartilhada pelos widgets desta janela."
                        color: "white"
                    }
                }
            }
        }
    }
}
