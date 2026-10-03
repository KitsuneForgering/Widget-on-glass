QSB ?= /usr/lib/qt6/bin/qsb
QML ?= /usr/lib/qt6/bin/qml

.PHONY: build check render-check demo
build: shaders/glass.frag.qsb

shaders/glass.frag.qsb: shaders/glass.frag
	$(QSB) --glsl '100 es,120,150' --hlsl 50 --msl 12 -o $@ $<

check: build
	python3 tests/check.py
	omarchy plugin validate .
	/usr/lib/qt6/bin/qmllint LiquidGlass.qml Preview.qml tests/render.qml

# A short-lived window is needed: this Qt's offscreen backend uses the software scenegraph.
render-check: check
	QT_QPA_PLATFORM=wayland QT_QPA_PLATFORMTHEME= QT_QUICK_CONTROLS_STYLE=Basic QT_FORCE_STDERR_LOGGING=1 timeout 15s $(QML) tests/render.qml
	python3 tests/check.py --render

demo: build
	quickshell -p .
