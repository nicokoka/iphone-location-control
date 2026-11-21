#!/usr/bin/env bash
# Sets up the environment, starts the iPhone tunnel, and opens the web UI.
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(uname)" != "Darwin" ]; then
  echo "This tool only runs on macOS." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh and run this again." >&2
  exit 1
fi

PY="$(brew --prefix)/bin/python3.12"
if [ ! -x "$PY" ]; then
  echo "Installing Python 3.12 with Homebrew..."
  brew install python@3.12
fi

if [ ! -x .venv/bin/pymobiledevice3 ]; then
  echo "Setting up (first run only, takes a few minutes)..."
  "$PY" -m venv .venv
  .venv/bin/pip install --upgrade pip >/dev/null
  .venv/bin/pip install -r requirements.txt
fi
export PATH="$PWD/.venv/bin:$PATH"

if [ "$(pymobiledevice3 usbmux list 2>/dev/null | tr -d '[:space:]')" = "[]" ]; then
  echo "No iPhone found. Plug it in with a data cable, unlock it, and tap 'Trust'." >&2
  echo "See README.md > Troubleshooting." >&2
  exit 1
fi

LOG_FILE="${TMPDIR:-/tmp}/location-control-tunneld.log"
echo "Starting the iPhone tunnel (needs your Mac password)..."
sudo -v
sudo "$PWD/.venv/bin/pymobiledevice3" remote tunneld >"$LOG_FILE" 2>&1 &
TUNNEL_PID=$!

cleanup() {
  echo "Restoring real location and stopping..."
  pymobiledevice3 developer dvt simulate-location clear --tunnel '' >/dev/null 2>&1 || true
  sudo kill "$TUNNEL_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 3
(sleep 2 && open "http://127.0.0.1:5055") &
python -m spoofer.server
