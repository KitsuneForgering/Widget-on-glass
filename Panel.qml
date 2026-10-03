import QtQuick
import Quickshell
import Quickshell.Wayland

Item {
    id: root
    property var shell: null
    property var manifest: null
    property bool opened: false
    function open(_payload) { opened = true; Qt.callLater(function() { preview.forceActiveFocus() }) }
    function close() { opened = false }
    function dismiss() {
        if (shell) shell.hide(manifest ? manifest.id : "kitsuneforgering.widget-on-glass")
        else close()
    }

    PanelWindow {
        visible: root.opened
        implicitWidth: 640
        implicitHeight: 480
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "widget-on-glass-preview"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
        Preview {
            id: preview
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: root.dismiss()
            onDismissed: root.dismiss()
        }
    }
}
