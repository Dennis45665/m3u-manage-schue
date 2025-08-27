#!/usr/bin/env bash
set -euo pipefail

# Änderung: Projektverzeichnis dynamisch relativ zu diesem Skript ermitteln,
# damit kein harter Pfad mehr angepasst werden muss.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_DIR="$(realpath "${SCRIPT_DIR}/..")"

echo "[tg_bot] Projektverzeichnis: ${PROJECT_DIR}"
cd "${PROJECT_DIR}"

# Änderung: venv-Python bevorzugen, sonst auf systemweites python3 zurückfallen
VENV_PYTHON="${PROJECT_DIR}/venv/bin/python"

if [[ -x "${VENV_PYTHON}" ]];
then
  PY="${VENV_PYTHON}"
  echo "[tg_bot] Verwende venv Python: ${PY}"
else
  # Fallback auf systemweites python3
  if command -v python3 >/dev/null 2>&1; then
    PY="python3"
    echo "[tg_bot] venv Python nicht gefunden. Fallback: ${PY}"
  else
    echo "[tg_bot] Fehler: Weder venv Python noch python3 vorhanden." >&2
    exit 1
  fi
fi

echo "[tg_bot] Starte Modul: tg_bot.main_tg"
exec "${PY}" -m tg_bot.main_tg
