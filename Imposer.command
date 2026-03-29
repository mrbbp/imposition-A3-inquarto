#!/bin/bash
# Double-clic : impose tous les PDF du dossier (à côté de ce fichier), hors *_impose_A3.pdf.
# Pour chaque fichier : k est déduit ; si le nombre de pages n’est pas un multiple de 8,
# des pages blanches sont ajoutées **en fin de livret** (--pad-blanks, sans modifier le source).
# Pour refuser ce complément : INQUARTO_STRICT_PAGES=1 avant le lancement.
# Scripts dans .inquarto/ ; venv .inquarto/.venv (créé / dépendances si besoin).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PKG="${ROOT}/.inquarto"
PY="${PKG}/.venv/bin/python"
REQ="${PKG}/requirements.txt"
IMPOSE="${PKG}/impose_quarto.py"
PYTHON_BIN="${PYTHON:-/usr/bin/python3}"

cd "$ROOT"

if [[ ! -f "$IMPOSE" ]]; then
  echo "Fichier impose_quarto.py introuvable dans : $PKG" >&2
  exit 1
fi
if [[ ! -f "$REQ" ]]; then
  echo "Fichier requirements.txt introuvable dans : $PKG" >&2
  exit 1
fi

if [[ ! -x "$PY" ]]; then
  echo "→ création du venv (${PYTHON_BIN})…"
  "$PYTHON_BIN" -m venv "${PKG}/.venv"
fi

if ! "$PY" -c "import fitz" 2>/dev/null; then
  echo "→ installation des dépendances (PyMuPDF, etc.)…"
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r "$REQ"
fi

echo "Dossier projet : $ROOT"
echo "→ Imposition in quarto : k = pages / 8 ; si besoin, pages blanches en fin de livret (multiple de 8)."
echo "→ Fichiers traités : *.pdf ici (sauf *_impose_A3.pdf)."
PAD=(--pad-blanks)
if [[ "${INQUARTO_STRICT_PAGES:-0}" == "1" || "${INQUARTO_STRICT_PAGES:-0}" == "yes" ]]; then
  PAD=()
  echo "→ Mode strict : multiple de 8 obligatoire (INQUARTO_STRICT_PAGES=1), pas de pages blanches ajoutées."
fi
echo ""
echo "→ Chaque fichier traité affiche un résumé : encart « pages en fin de pagination », puis tableau."
echo ""

if ((${#PAD[@]} > 0)); then
  "$PY" "$IMPOSE" "${PAD[@]}"
else
  "$PY" "$IMPOSE"
fi
code=$?

echo ""
if [[ "$code" -eq 0 ]]; then
  echo "Terminé."
else
  echo "Terminé avec erreur(s) — voir ci-dessus (code $code)." >&2
fi
read -r -p "Entrée pour fermer… " _

exit "$code"
