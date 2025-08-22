#!/bin/bash

# Der absolute Pfad zum Projektverzeichnis auf deinem Server
# WICHTIG: Diesen Pfad musst du anpassen!
PROJECT_DIR="/home/jellyfin/m3u-manage-schue"

# In das Projektverzeichnis wechseln. Das ist entscheidend, damit Python die Module findet.
cd "$PROJECT_DIR" || exit

# Pfad zum Python-Interpreter im virtuellen Environment
VENV_PYTHON="venv/bin/python"

# Das Skript als Modul ausführen. Das löst das Import-Problem.
"$VENV_PYTHON" -m tg_bot.main_tg
