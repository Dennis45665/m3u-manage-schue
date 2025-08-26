#!/bin/bash
# Navigiere zum Skript-Verzeichnis
cd "$(dirname "$0")"

# Prüfe, ob das venv-Verzeichnis existiert
if [ -d "venv" ]; then
    # Aktiviere das virtuelle Environment
    source venv/bin/activate
else
    echo "Virtuelles Environment 'venv' nicht gefunden. Bitte zuerst das Haupt-Skript ausführen."
    exit 1
fi

# Führe das Python-Skript mit python3 aus
python3 cleaner.py

# Deaktiviere das virtuelle Environment
deactivate
