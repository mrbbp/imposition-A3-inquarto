#!/usr/bin/env python3
"""
Impose un PDF (143,5×205 mm) sur des feuilles A3 (in quarto imbriqué).

**k** = feuilles A3 = **pages / 8** (multiple de 8, **≥ 8**). Les tables sont **générées** par
`layouts_dynamic.py` (plus de fichiers de layout figés par taille).

Grille 2×2 : marge 5 mm ; copie 1:1.

Usage:
  python impose_quarto.py "livret.pdf" sortie.pdf
  python impose_quarto.py                       # batch
  python impose_quarto.py --pad-blanks livret.pdf sortie.pdf   # complète en multiple de 8 (blancs en fin)
  python impose_quarto.py --proof-only epreuve.pdf --k 2   # 16 p.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

from layouts_dynamic import generate_sheets_bord_court, generate_sheets_bord_long

# Dossier du paquet (.inquarto) ; les PDF « batch » sans argument sont cherchés un niveau au-dessus
PACKAGE_DIR = Path(__file__).resolve().parent
PDF_WORK_DIR = PACKAGE_DIR.parent

# A3 portrait (points, 72 dpi)
A3_W_PT = 297.0 / 25.4 * 72.0
A3_H_PT = 420.0 / 25.4 * 72.0

PAGE_W_MM = 143.5
PAGE_H_MM = 205.0


def _mm_to_pt(mm: float) -> float:
    return mm / 25.4 * 72.0


PAGE_W_PT = _mm_to_pt(PAGE_W_MM)
PAGE_H_PT = _mm_to_pt(PAGE_H_MM)

MARGIN_X_PT = (A3_W_PT - 2.0 * PAGE_W_PT) / 2.0
MARGIN_Y_PT = (A3_H_PT - 2.0 * PAGE_H_PT) / 2.0

_FMT_TOL_PT = 2.0


def padded_page_count(n: int) -> int:
    """Nombre de pages après complément par des blancs en fin (multiple de 8, ≥ n)."""
    if n <= 0:
        raise ValueError("Le document ne contient aucune page.")
    return ((n + 7) // 8) * 8


def k_from_page_count(n: int) -> int:
    """
    Déduit k (feuilles A3) : **k = n / 8**. Il faut **n ≥ 8** et **n multiple de 8**.
    """
    if n <= 0:
        raise ValueError("Le document ne contient aucune page.")
    if n < 8:
        raise ValueError(
            f"Nombre de pages ({n}) : il faut au moins **8 pages** (une feuille A3 in quarto)."
        )
    if n % 8 != 0:
        raise ValueError(
            f"Nombre de pages ({n}) : il faut un **multiple de 8** "
            f"(k = pages / 8 feuilles A3), ou utiliser **--pad-blanks**."
        )
    return n // 8


def _sheets_for_page_count(n: int, pli_premier: str) -> list:
    if pli_premier == "bord-court":
        return generate_sheets_bord_court(n)
    if pli_premier == "bord-long":
        return generate_sheets_bord_long(n)
    raise ValueError(f"pli_premier inconnu : {pli_premier!r}")


def validate_manuscript_pdf(
    path: Path,
    *,
    pad_blanks: bool = False,
) -> tuple[list[str], int | None]:
    """
    Contrôles avant imposition. Retourne (erreurs, nombre de pages du fichier si OK).

    Si ``pad_blanks`` est vrai, le multiple de 8 est vérifié **après** complément par des
    pages blanches en fin (voir ``padded_page_count``).
    """
    errors: list[str] = []
    if not path.exists():
        return ["Fichier introuvable."], None
    if not path.is_file():
        return ["Ce n'est pas un fichier."], None
    if path.suffix.lower() != ".pdf":
        return ["Extension attendue : .pdf"], None

    try:
        doc = fitz.open(path)
    except RuntimeError as e:
        return [f"Impossible d'ouvrir le PDF : {e}"], None

    try:
        n = len(doc)
        if n == 0:
            return ["Le PDF ne contient aucune page."], None

        n_check = padded_page_count(n) if pad_blanks else n
        try:
            k_from_page_count(n_check)
        except ValueError as e:
            return [str(e)], None

        for i in range(n):
            r = doc[i].rect
            pw, ph = r.width, r.height
            if pw <= 0 or ph <= 0:
                errors.append(f"Page {i + 1} : dimensions invalides.")
                break
            if pw > ph + 8.0:
                errors.append(
                    f"Page {i + 1} : format paysage ({pw:.0f}×{ph:.0f} pt) — "
                    f"attendu portrait {PAGE_W_MM}×{PAGE_H_MM} mm."
                )
                break
            if abs(pw - PAGE_W_PT) > _FMT_TOL_PT or abs(ph - PAGE_H_PT) > _FMT_TOL_PT:
                errors.append(
                    f"Page {i + 1} : {pw:.1f}×{ph:.1f} pt — attendu "
                    f"{PAGE_W_MM}×{PAGE_H_MM} mm ({PAGE_W_PT:.1f}×{PAGE_H_PT:.1f} pt, tolérance ±{_FMT_TOL_PT:.0f} pt). "
                    "Pas de redimensionnement à l’imposition : le gabarit doit correspondre exactement."
                )
                break
    finally:
        doc.close()

    if errors:
        return errors, None
    return [], n


def _default_imposed_path(src: Path) -> Path:
    return src.parent / f"{src.stem}_impose_A3.pdf"


def manuscript_pdfs_in_work_dir() -> list[Path]:
    found: list[Path] = []
    for path in sorted(PDF_WORK_DIR.iterdir(), key=lambda x: x.name.lower()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        if path.name.endswith("_impose_A3.pdf"):
            continue
        found.append(path)
    return found


# Affichage terminal : uniquement résumé « humain » (encart pagination + tableau)
_SUMMARY_W = 78
# Ligne tableau : 6 + lw + 3 + rw + 2 = 11 + lw + rw (= 78 si lw+rw = 67)
_TBL_LW = 28
_TBL_RW = 39
_IND4 = "    "
# Largeur utile entre « ## » et « ## » sur une ligne d’encart (78 car. total)
_ENC_INNER = 68


def _tbl_fit(s: str, max_len: int) -> str:
    s = " ".join(s.split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _encart_line(inner: str) -> str:
    """Une ligne d’encart ## … ## (78 car. avec marge gauche)."""
    t = _tbl_fit(inner, _ENC_INNER)
    return f"{_IND4}## {t:<{_ENC_INNER}} ##"


def _print_encart_fin_pagination(pad: int, n_src: int, n_imp: int) -> None:
    """Encart visuel : fin de pagination du livret (pages blanches virtuelles n_src+1 … n_imp si besoin)."""
    bar = _IND4 + "#" * (_SUMMARY_W - 4)
    print(bar)
    if pad > 0:
        print(_encart_line("PAGES AJOUTÉES EN FIN DE PAGINATION (après le contenu)"))
        p0, p1 = n_src + 1, n_imp
        print(
            _encart_line(
                f"+{pad} page(s) blanche(s) — fin de livret : pages {p0} à {p1}"
            )
        )
    else:
        print(_encart_line("FIN DE PAGINATION — aucune page blanche ajoutée"))
        print(
            _encart_line(
                f"Le PDF compte déjà {n_src} pages (multiple de 8), rien à compléter."
            )
        )
    print(bar)
    print()


def print_imposition_human_summary(
    src: Path,
    out_path: Path,
    *,
    n_src: int,
    n_imp: int,
    k: int,
) -> None:
    """
    Résumé lisible : encart « fin de pagination » puis tableau fichier / k / sortie.
    """
    pad = n_imp - n_src
    lw, rw = _TBL_LW, _TBL_RW

    print()

    _print_encart_fin_pagination(pad, n_src, n_imp)

    top = "    +-" + "-" * lw + "-+-" + "-" * rw + "-+"
    row = lambda a, b: (
        "    | "
        + f"{_tbl_fit(a, lw):<{lw}}"
        + " | "
        + f"{_tbl_fit(b, rw):<{rw}}"
        + " |"
    )

    rows: list[tuple[str, str]] = [
        ("Fichier source (PDF)", src.name),
        ("Pages dans le PDF source", str(n_src)),
        ("Total pages (imposition)", str(n_imp)),
        ("k — feuilles A3 recto-verso", str(k)),
        ("Fichier A3 généré", out_path.name),
    ]

    print(top)
    print(row("Indication", "Valeur"))
    print("    +-" + "-" * lw + "-+-" + "-" * rw + "-+")
    for left, right in rows:
        print(row(left, right))
    print(top)
    print()


def _print_imposition_success(
    src: Path,
    out_path: Path,
    *,
    n_src: int,
    n_imp: int,
    k: int,
    human_summary: bool,
) -> None:
    if human_summary:
        print_imposition_human_summary(
            src, out_path, n_src=n_src, n_imp=n_imp, k=k
        )
    else:
        extra = ""
        if n_imp > n_src:
            extra = f", +{n_imp - n_src} p. blanche(s) en fin"
        print(f"Imposé : {out_path}  (k={k}, {n_src} p. source → {n_imp} p.{extra})")


def _cell_rect(col: int, row: int) -> fitz.Rect:
    x0 = MARGIN_X_PT + col * PAGE_W_PT
    y0 = MARGIN_Y_PT + row * PAGE_H_PT
    return fitz.Rect(x0, y0, x0 + PAGE_W_PT, y0 + PAGE_H_PT)


def _draw_face(
    dst_page: fitz.Page,
    src: fitz.Document,
    face: list[list[tuple[int, int]]],
) -> None:
    for row in range(2):
        for col in range(2):
            pno_1, rot = face[row][col]
            pno = pno_1 - 1
            if pno < 0 or pno >= len(src):
                raise IndexError(f"Page manuscrit absente : {pno_1} (doc a {len(src)} pages)")
            dest = _cell_rect(col, row)
            pr = src[pno].rect
            dst_page.show_pdf_page(dest, src, pno, rotate=rot, clip=pr)


def _open_manuscript_with_optional_padding(
    src_path: Path,
    *,
    pad_blanks: bool,
    n_original: int,
) -> fitz.Document:
    """Document prêt pour l’imposition (pages blanches en fin si ``pad_blanks`` et besoin)."""
    base = fitz.open(src_path)
    n_target = padded_page_count(n_original) if pad_blanks else n_original
    pad = n_target - n_original
    if pad <= 0:
        return base
    ref = base[0].rect
    for _ in range(pad):
        base.new_page(width=ref.width, height=ref.height)
    return base


def impose(
    src_path: Path,
    out_path: Path,
    *,
    pli_premier: str = "bord-court",
    pad_blanks: bool = False,
) -> tuple[int, int, int]:
    """Retourne (k, nombre de pages source, nombre de pages après complément éventuel)."""
    errs, n = validate_manuscript_pdf(src_path, pad_blanks=pad_blanks)
    if errs:
        raise ValueError("\n".join(errs))
    assert n is not None
    n_impose = padded_page_count(n) if pad_blanks else n
    k = k_from_page_count(n_impose)

    sheets = _sheets_for_page_count(n_impose, pli_premier)
    src = _open_manuscript_with_optional_padding(
        src_path,
        pad_blanks=pad_blanks,
        n_original=n,
    )
    try:
        dst = fitz.open()
        try:
            for sheet in sheets:
                for side in ("front", "back"):
                    page = dst.new_page(width=A3_W_PT, height=A3_H_PT)
                    _draw_face(page, src, sheet[side])
            dst.save(out_path, garbage=4, deflate=True)
        finally:
            dst.close()
    finally:
        src.close()
    return k, n, n_impose


def make_proof_manuscript(out_path: Path, page_count: int) -> None:
    """page_count : multiple de 8, ≥ 8 (génère une épreuve pour imposer)."""
    k_from_page_count(page_count)
    doc = fitz.open()
    try:
        fs_main = min(110.0, PAGE_W_PT * 0.26)
        fs_sub = min(36.0, PAGE_H_PT * 0.06)
        for i in range(page_count):
            p = doc.new_page(width=PAGE_W_PT, height=PAGE_H_PT)
            num = str(i + 1)
            p.insert_text(
                (PAGE_W_PT * 0.22, PAGE_H_PT * 0.35),
                num,
                fontsize=fs_main,
                color=(0, 0, 0),
            )
            p.insert_text(
                (PAGE_W_PT * 0.38, PAGE_H_PT * 0.55),
                "haut \u2191",
                fontsize=fs_sub,
                color=(0.6, 0, 0),
            )
        doc.save(out_path, garbage=4, deflate=True)
    finally:
        doc.close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=f"Imposition in quarto ({PAGE_W_MM}×{PAGE_H_MM} mm) : pages = 8×k, tables générées automatiquement."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help=f"PDF manuscrit ({PAGE_W_MM}×{PAGE_H_MM} mm), nombre de pages multiple de 8 (≥ 8) ; "
        "omis = traiter tous les PDF du dossier du projet",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="PDF A3 imposé ; défaut avec input seul : <input_stem>_impose_A3.pdf",
    )
    parser.add_argument(
        "--proof-output",
        type=Path,
        metavar="PDF",
        help="Génère un manuscrit épreuve puis impose vers ce fichier (taille : --k, défaut 4 → 32 p.)",
    )
    parser.add_argument(
        "--proof-only",
        type=Path,
        metavar="OUT",
        help="Ne génère que le PDF manuscrit épreuve (taille : --k, défaut 4 → 32 p.)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=4,
        metavar="K",
        help="Pour --proof-only / --proof-output : nombre de feuilles A3 (pages = 8×k). Défaut : 4 (32 p.). k ≥ 1.",
    )
    parser.add_argument(
        "--pli-premier",
        choices=("bord-court", "bord-long"),
        default="bord-court",
        help="Ordre des plis sur l'A3 portrait : bord-court = d'abord haut/bas puis gauche/droite (défaut) ; "
        "bord-long = d'abord gauche/droite puis haut/bas.",
    )
    parser.add_argument(
        "--pad-blanks",
        action="store_true",
        help="Si le nombre de pages n’est pas un multiple de 8 : ajouter des pages blanches **en fin de livret** "
        "pour atteindre le multiple de 8 supérieur (sans modifier le fichier source).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Sortie compacte (une ligne par fichier) sans le bloc étoiles + tableau « lecture humaine ».",
    )
    args = parser.parse_args(argv)

    if args.k < 1:
        parser.error("--k doit être ≥ 1 (nombre de feuilles A3).")
    proof_pages = 8 * args.k

    if args.proof_only:
        make_proof_manuscript(args.proof_only, proof_pages)
        print(f"Épreuve manuscrit ({proof_pages} p., k={args.k}) : {args.proof_only}")
        return 0

    if args.proof_output:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            make_proof_manuscript(tmp_path, proof_pages)
            try:
                impose(
                    tmp_path,
                    args.proof_output,
                    pli_premier=args.pli_premier,
                    pad_blanks=False,
                )
            except ValueError as e:
                print(str(e), file=sys.stderr)
                return 1
            print(f"Imposé (épreuve k={args.k}) : {args.proof_output}")
        finally:
            tmp_path.unlink(missing_ok=True)
        return 0

    if args.input is None and args.output is None:
        candidates = manuscript_pdfs_in_work_dir()
        if not candidates:
            print(
                "Aucun PDF manuscrit dans le dossier du projet (à côté de Imposer.command) :\n"
                f"  {PDF_WORK_DIR}\n"
                "(dépose un .pdf ici ; les fichiers *_impose_A3.pdf sont ignorés).",
                file=sys.stderr,
            )
            return 1
        err_count = 0
        for src in candidates:
            outp = _default_imposed_path(src)
            try:
                k, n, n_imp = impose(
                    src,
                    outp,
                    pli_premier=args.pli_premier,
                    pad_blanks=args.pad_blanks,
                )
                _print_imposition_success(
                    src,
                    outp,
                    n_src=n,
                    n_imp=n_imp,
                    k=k,
                    human_summary=not args.quiet,
                )
            except ValueError as e:
                err_count += 1
                print(f"{src.name} : {e}", file=sys.stderr)
        return 1 if err_count else 0

    if args.input is None:
        parser.error(
            "Indique un fichier PDF d'entrée, ou lance sans argument pour traiter les PDF du dossier du projet."
        )

    out_path = args.output if args.output is not None else _default_imposed_path(args.input)

    try:
        k, n, n_imp = impose(
            args.input,
            out_path,
            pli_premier=args.pli_premier,
            pad_blanks=args.pad_blanks,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    _print_imposition_success(
        args.input,
        out_path,
        n_src=n,
        n_imp=n_imp,
        k=k,
        human_summary=not args.quiet,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
