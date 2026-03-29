#!/bin/bash
# Double-clic dans le Finder pour ouvrir l’interface InQuarto (macOS).
# Venv : .inquarto/.venv (créé et dépendances installées si besoin).

set -euo pipefail
PKG="$(cd "$(dirname "$0")" && pwd)"
PY="${PKG}/.venv/bin/python"
REQ="${PKG}/requirements.txt"
PYTHON_BIN="${PYTHON:-/usr/bin/python3}"

cd "$PKG"

if [[ ! -x "$PY" ]]; then
  echo "→ création du venv (${PYTHON_BIN})…"
  "$PYTHON_BIN" -m venv "${PKG}/.venv"
fi

if ! "$PY" -c "import fitz" 2>/dev/null || ! "$PY" -c "import tkinterdnd2" 2>/dev/null; then
  echo "→ installation des dépendances…"
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r "$REQ"
fi

if ! "$PY" -c "import tkinter" 2>/dev/null; then
  osascript -e 'display alert "InQuarto — Tkinter" message "Ce Python n’inclut pas Tk (souvent le cas avec Homebrew). Recrée le venv avec le Python Apple :\\n\\nrm -rf .venv\\n/usr/bin/python3 -m venv .venv\\npuis relance ce fichier."'
  exit 1
fi

exec "$PY" "${PKG}/in_quarto_gui.py"
