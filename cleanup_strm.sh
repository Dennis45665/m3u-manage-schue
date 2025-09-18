#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(dirname "$(readlink -f "$0")")"
echo "Projektordner: $PROJECT_DIR"

VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
SCRIPT="$PROJECT_DIR/src/cleanup_strm_folders.py"

if [ ! -d "$VENV_DIR" ]; then
  echo "Kein virtuelles Environment gefunden. Erstelle venv ..."
  python3 -m venv "$VENV_DIR"
  "$VENV_PYTHON" -m pip install --upgrade pip
  if [ -f "$REQUIREMENTS" ]; then
    "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"
  fi
else
  echo "Virtuelles Environment gefunden, benutze bestehendes."
fi

echo "Starte Cleanup .strm-Ordner ..."
exec "$VENV_PYTHON" "$SCRIPT"

