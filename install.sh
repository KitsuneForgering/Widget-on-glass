#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./install.sh [--prepare-only] [--prefix DIRECTORY]

Clone the Omarchy source matching the installed package, apply Widget on Glass,
and point Omarchy at the checkout. Reboot separately to activate the new shell.
--prepare-only creates the patched checkout without changing the active Omarchy.
EOF
}

prepare_only=false
prefix="${XDG_DATA_HOME:-$HOME/.local/share}/widget-on-glass"
while (($#)); do
  case "$1" in
    --prepare-only) prepare_only=true; shift ;;
    --prefix)
      (($# >= 2)) || { usage >&2; exit 2; }
      prefix=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

for command_name in git pacman python3 omarchy /usr/lib/qt6/bin/qsb; do
  command -v "$command_name" >/dev/null || {
    echo "Missing required command: $command_name" >&2
    exit 1
  }
done

version=$(pacman -Q omarchy | awk '{print $2}')
version=${version%-*}
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "Unsupported Omarchy package version: $version" >&2
  exit 1
}

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p -- "$prefix"
prefix=$(realpath -e -- "$prefix")
target="$prefix/omarchy-v$version"
if [[ -e $target ]]; then
  if [[ ! -f $target/shell/Ui/GlassOverlay.qml ]] ||
     [[ ! -f $target/shell/Ui/shaders/overlay.frag.qsb ]] ||
     [[ $(git -C "$target" describe --tags --exact-match 2>/dev/null || true) != "v$version" ]]; then
    echo "Checkout already exists and is not a prepared Widget on Glass install: $target" >&2
    exit 1
  fi
  echo "Using prepared checkout: $target"
else
  stage=$(mktemp -d -- "$prefix/.omarchy-glass.XXXXXX")
  trap 'rm -rf -- "$stage"' EXIT
  git clone --depth 1 --branch "v$version" https://github.com/basecamp/omarchy.git "$stage/source"
  python3 -B "$project_root/integrations/omarchy/apply.py" "$stage/source"
  mv -- "$stage/source" "$target"
  rmdir -- "$stage"
  trap - EXIT
  echo "Patched Omarchy checkout: $target"
fi
if [[ $prepare_only == false ]]; then
  omarchy dev link "$target" --no-reboot
  echo "Reboot to activate the checkout. Restore the package with: omarchy dev unlink"
fi
