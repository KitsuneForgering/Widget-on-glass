import QtQuick
import QtQuick.Shapes

// Full-window veil with a rounded hole under the glass card, so the card shows
// the blurred desktop instead of blur, veil and tint stacked on each other.
Shape {
    id: root
    property color color: "transparent"
    property Rectangle hole
    property real radius: hole ? hole.radius : 0

    anchors.fill: parent
    preferredRendererType: Shape.CurveRenderer

    ShapePath {
        fillColor: root.color
        strokeWidth: -1
        fillRule: ShapePath.OddEvenFill
        PathRectangle { width: root.width; height: root.height }
        PathRectangle {
            x: root.hole ? root.hole.x : 0
            y: root.hole ? root.hole.y : 0
            width: root.hole && root.hole.visible ? root.hole.width : 0
            height: root.hole && root.hole.visible ? root.hole.height : 0
            radius: root.radius
        }
    }
}
