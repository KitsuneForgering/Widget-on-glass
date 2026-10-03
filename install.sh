#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./install.sh [--prepare-only | --reload-only] [--prefix DIRECTORY]

Clone the Omarchy source matching the installed package, apply Widget on Glass,
and point Omarchy at the checkout. Reload the shell in the current session.
--prepare-only creates the patched checkout without changing the active Omarchy.
--reload-only reloads an already linked checkout without running sudo again.
EOF
}

prepare_only=false
reload_only=false
prefix="${XDG_DATA_HOME:-$HOME/.local/share}/widget-on-glass"
while (($#)); do
  case "$1" in
    --prepare-only) prepare_only=true; shift ;;
    --reload-only) reload_only=true; shift ;;
    --prefix)
      (($# >= 2)) || { usage >&2; exit 2; }
      prefix=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
if [[ $prepare_only == true && $reload_only == true ]]; then
  usage >&2
  exit 2
fi

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
if [[ $reload_only == true && ! -e $target ]]; then
  echo "No prepared checkout at $target; run ./install.sh first." >&2
  exit 1
fi
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
reload_shell() {
  for command_name in hyprctl quickshell setsid timeout; do
    command -v "$command_name" >/dev/null || {
      echo "Missing required command for shell reload: $command_name" >&2
      return 1
    }
  done
  if [[ -z ${WAYLAND_DISPLAY:-} ]] || ! hyprctl -j monitors >/dev/null 2>&1; then
    echo "No active Hyprland session; reboot or log in to load the checkout."
    return 0
  fi
  if "$target/bin/omarchy-hyprland-session-locked"; then
    echo "Refusing to reload the shell while the session is locked." >&2
    return 1
  fi

  # omarchy restart shell reads the old session path until the next login.
  # Use its Quickshell stop mechanism, then launch the linked tree explicitly.
  current_path=$(systemctl --user show-environment 2>/dev/null | sed -n 's/^OMARCHY_PATH=//p' | tail -n 1) || true
  current_path=${current_path:-${OMARCHY_PATH:-/usr/share/omarchy}}
  for shell_path in "$current_path/shell" "$target/shell"; do
    while timeout 5 quickshell kill -p "$shell_path" --any-display >/dev/null 2>&1; do :; done
  done

  setsid -f env OMARCHY_PATH="$target" PATH="$target/bin:$PATH" \
    "$target/bin/omarchy-launch-shell" >/dev/null 2>&1
  for ((attempt = 0; attempt < 30; attempt++)); do
    if OMARCHY_PATH="$target" "$target/bin/omarchy-shell" shell ping >/dev/null 2>&1; then
      echo "Widget on Glass shell is running from $target"
      return 0
    fi
    sleep 0.2
  done

  echo "The new shell did not become ready; restoring the previous shell." >&2
  while timeout 5 quickshell kill -p "$target/shell" --any-display >/dev/null 2>&1; do :; done
  omarchy restart shell || true
  return 1
}

if [[ $reload_only == true ]]; then
  if [[ ! -f /etc/omarchy.conf ]]; then
    echo "Omarchy has no dev link; run ./install.sh first." >&2
    exit 1
  fi
  configured=$(OMARCHY_PATH=; . /etc/omarchy.conf; printf '%s' "$OMARCHY_PATH")
  if [[ $configured != "$target" ]]; then
    echo "Omarchy is not linked to $target; run ./install.sh first." >&2
    exit 1
  fi
elif [[ $prepare_only == false ]]; then
  omarchy dev link "$target" --no-reboot
fi
if [[ $prepare_only == false ]]; then
  reload_shell
  echo "Reboot later to align Hyprland and system services with this checkout. Restore the package with: omarchy dev unlink"
fi
