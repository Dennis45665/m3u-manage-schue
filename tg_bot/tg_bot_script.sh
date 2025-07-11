#!/bin/bash

# Ordner, in dem das Script liegt, also /project-root/tg_bot
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

echo "Script-Ordner: $SCRIPT_DIR"

# Projektordner eine Ebene höher, also /project-root
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Projekt-Ordner: $PROJECT_DIR"

# Pfad zum virtuellen Environment (im Projektordner)
VENV_DIR="$PROJECT_DIR/venv"

# Pfad zum Python-Interpreter im virtuellen Environment
VENV_PYTHON="$VENV_DIR/bin/python"

# Pfad zur requirements.txt (im Projektordner)
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

# Python-Skript (liegt im gleichen Ordner wie das .sh-Skript)
SCRIPT="$SCRIPT_DIR/tg_bot_script.py"

# Prüfen, ob venv existiert, ansonsten anlegen
if [ ! -d "$VENV_DIR" ]; then
  echo "Kein virtuelles Environment gefunden. Erstelle venv ..."
  python3 -m venv "$VENV_DIR"

  echo "Aktiviere venv und installiere Abhängigkeiten..."
  "$VENV_PYTHON" -m pip install --upgrade pip
  if [ -f "$REQUIREMENTS" ]; then
    "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"
  else
    echo "WARNUNG: requirements.txt nicht gefunden!"
  fi
else
  echo "Virtuelles Environment gefunden, benutze bestehendes."
fi

# Python-Skript mit venv-Python ausführen
echo "Starte TG-Jellyfin-Skript ..."
"$VENV_PYTHON" "$SCRIPT"
