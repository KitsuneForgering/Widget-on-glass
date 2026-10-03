#!/usr/bin/env bash
set -euo pipefail

qsb="${QSB:-/usr/lib/qt6/bin/qsb}"
"$qsb" --glsl '100 es,120,150' --hlsl 50 --msl 12 -o src/shaders/glass.frag.qsb src/shaders/glass.frag
"$qsb" --glsl '100 es,120,150' --hlsl 50 --msl 12 -o src/shaders/overlay.frag.qsb src/shaders/overlay.frag
/usr/lib/qt6/bin/qmllint src/GlassWidget.qml src/GlassOverlay.qml src/GlassLens.qml src/GlassScrim.qml src/render.qml
python3 checks/contrast.py
python3 -B checks/lens.py

case "${1:-}" in
    run) quickshell -p src ;;
    render-check)
        quickshell -p src/render.qml
        python3 checks/check.py
        ;;
esac
