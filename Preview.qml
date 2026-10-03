pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    implicitWidth: 640
    implicitHeight: 480
    signal dismissed()
    property bool darkBackdrop: false
    property bool expanded: false
    property real refractionThickness: 36
    property real contentRefraction: 0.45
    readonly property color backdropTextColor: darkBackdrop ? "white" : "#172334"
    property alias glassEnabled: enableGlass.checked
    readonly property color backdropColor: darkBackdrop ? "#172334" : "#eef2f6"
    color: "#eef2f6"

    Rectangle {
        id: backdrop
        anchors.fill: parent
        color: root.darkBackdrop ? "#172334" : "#eef2f6"
        Repeater {
            model: 32
            Rectangle {
                required property int index
                x: index * root.width / 32
                width: 1
                height: root.height
                color: root.darkBackdrop ? "#304356" : "#d7dfe8"
            }
        }
        Column {
            anchors.centerIn: parent
            spacing: 12
            Text {
                text: "12:45"
                font.pixelSize: 44
                font.bold: true
                color: root.backdropTextColor
                style: Text.Sunken
                styleColor: "#50000000"
            }
            Text {
                text: "Este item está atrás do vidro.\nSeu texto continua nítido."
                font.pixelSize: 18
                color: root.backdropTextColor
                style: Text.Sunken
                styleColor: "#50000000"
            }
        }
    }

    ShaderEffectSource {
        id: sharedBackdrop
        visible: false
        sourceItem: backdrop
        sourceRect: Qt.rect(0, 0, root.width, root.height)
        live: true
    }

    Column {
        x: 16
        y: 8
        width: root.width - 32
        Row {
            spacing: 8
            CheckBox { id: enableGlass; text: "Vidro"; checked: true; palette.windowText: "#172334" }
            CheckBox { id: reduceMotion; text: "Menos movimento"; palette.windowText: "#172334" }
            Button { text: "Fundo claro/escuro"; onClicked: root.darkBackdrop = !root.darkBackdrop }
        }
        Slider {
            width: parent.width
            from: 0
            to: 80
            value: root.refractionThickness
            onMoved: root.refractionThickness = value
            Accessible.name: "Intensidade da refração nas bordas"
        }
    }

    LiquidGlass {
        id: mainGlass
        x: (root.width - width) / 2
        y: (root.height - height) / 2 + 24
        width: Math.max(1, root.width - (root.expanded ? 48 : 96))
        height: root.expanded ? 320 : 280
        radius: root.expanded ? 32 : 24
        sourceItem: backdrop
        sharedSource: sharedBackdrop
        backdropColor: root.backdropColor
        glassEnabled: enableGlass.checked
        thickness: root.refractionThickness
        contentRefraction: root.contentRefraction
        reducedMotion: reduceMotion.checked
        pressed: expandButton.down || closeButton.down

        // Local opaque label plate protects foreground without darkening the source.
        Rectangle {
            x: 16
            y: 16
            width: title.implicitWidth + 20
            height: title.implicitHeight + 12
            radius: 8
            color: mainGlass.contentPlateColor
            Text { id: title; anchors.centerIn: parent; text: "Fundo preservado"; color: mainGlass.contentColor; font.bold: true }
        }
        Row {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 16
            spacing: 8
            Button { id: expandButton; text: root.expanded ? "Recolher" : "Expandir"; onClicked: root.expanded = !root.expanded }
            Button { id: closeButton; text: "Fechar"; onClicked: root.dismissed() }
        }
    }

    LiquidGlass {
        id: sharedGlass
        x: 16
        y: root.height - 48
        width: 170
        height: 36
        radius: 18
        bevel: 8
        sourceItem: backdrop
        sharedSource: sharedBackdrop
        backdropColor: root.backdropColor
        glassEnabled: enableGlass.checked
        thickness: root.refractionThickness
        contentRefraction: root.contentRefraction
        reducedMotion: reduceMotion.checked
        Rectangle {
            anchors.centerIn: parent
            width: label.implicitWidth + 16
            height: label.implicitHeight + 8
            radius: 6
            color: sharedGlass.contentPlateColor
            Text { id: label; anchors.centerIn: parent; text: "Textura compartilhada"; color: sharedGlass.contentColor; font.pixelSize: 12 }
        }
    }
}
