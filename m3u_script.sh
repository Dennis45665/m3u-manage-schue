#!/bin/bash

# 1. Projektordner herausfinden (Ordner, in dem das Script liegt)
# $0 = Pfad zum Script, readlink -f macht daraus den absoluten Pfad,
# dirname entfernt die Dateiname, übrig bleibt nur der Ordner
PROJECT_DIR="$(dirname "$(readlink -f "$0")")"

echo "Projektordner: $PROJECT_DIR"

# 2. Pfad zum virtuellen Environment im Projektordner
VENV_DIR="$PROJECT_DIR/venv"

# 3. Pfad zum Python-Interpreter im virtuellen Environment
VENV_PYTHON="$VENV_DIR/bin/python"

# 4. Pfad zur requirements-Datei (im Projektordner erwartet)
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

# 5. Skript, das ausgeführt werden soll (relativ zum Projektordner)
SCRIPT="$PROJECT_DIR/main.py"

# 6. Prüfen, ob venv existiert
if [ ! -d "$VENV_DIR" ]; then
  echo "Kein virtuelles Environment gefunden. Erstelle venv ..."
  python3 -m venv "$VENV_DIR"

  echo "Aktiviere venv und installiere Abhängigkeiten..."
  # Paketinstallation im venv (pip)
  "$VENV_PYTHON" -m pip install --upgrade pip
  if [ -f "$REQUIREMENTS" ]; then
    "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS"
  else
    echo "WARNUNG: requirements.txt nicht gefunden!"
  fi
else
  echo "Virtuelles Environment gefunden, benutze bestehendes."
fi

# 7. Python-Skript mit venv-Python ausführen
echo "Starte M3U-Skript ..."
"$VENV_PYTHON" "$SCRIPT"

# venv deaktivieren
deactivate