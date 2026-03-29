#!/usr/bin/env python3
"""
InQuarto — interface graphique (macOS) : PDF 24 / 32 / 40 p. (143,5×205 mm), k déduit automatiquement.

Sans tkinterdnd2 : clic sur la zone pour choisir un fichier.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _HAVE_DND = True
except ImportError:
    _HAVE_DND = False

from impose_quarto import (
    PAGE_H_MM,
    PAGE_W_MM,
    impose,
    k_from_page_count,
    padded_page_count,
    validate_manuscript_pdf,
)


def _parse_drop_paths(data: str) -> list[Path]:
    data = data.strip()
    if not data:
        return []
    paths: list[Path] = []
    for m in re.finditer(r"\{([^}]*)\}|(\S+)", data):
        chunk = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if chunk:
            paths.append(Path(chunk))
    return paths


def _default_output_path(src: Path) -> Path:
    return src.parent / f"{src.stem}_impose_A3.pdf"


class InQuartoApp:
    def __init__(self) -> None:
        if _HAVE_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        self.root.title(f"InQuarto — 8×k p. {PAGE_W_MM}×{PAGE_H_MM} mm → A3")
        self.root.minsize(480, 320)
        self.root.geometry("560x380")

        self._pli = tk.StringVar(value="bord-court")
        self._pad_blanks = tk.BooleanVar(value=False)
        self._status = tk.StringVar(value="Prêt.")
        self._last_out: Path | None = None

        self._build()

    def _build(self) -> None:
        pad = {"padx": 14, "pady": 8}

        ttk.Label(
            self.root,
            text=f"Imposition in quarto (k = pages / 8 feuilles A3, pages ≥ 8 et multiple de 8, {PAGE_W_MM}×{PAGE_H_MM} mm)",
            font=("", 13, "bold"),
        ).pack(**pad)

        hint = (
            "Glissez un PDF ici"
            if _HAVE_DND
            else "tkinterdnd2 absent — cliquez pour choisir un fichier"
        )
        self._zone = tk.Frame(
            self.root,
            highlightbackground="#666",
            highlightthickness=2,
            bg="#f0f0f0",
        )
        self._zone.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        self._zone_lbl = tk.Label(
            self._zone,
            text=hint + "\n\n" + f"Exigences : {PAGE_W_MM}×{PAGE_H_MM} mm, nombre de pages ≥ 8 et multiple de 8 (8, 16, 24, …), ou cochez « Compléter en multiple de 8 » pour ajouter des pages blanches en fin de livret, pas de redimensionnement.",
            bg="#f0f0f0",
            fg="#333",
            justify=tk.CENTER,
            font=("", 12),
        )
        self._zone_lbl.pack(expand=True, fill=tk.BOTH)

        if _HAVE_DND:
            self._zone.drop_target_register(DND_FILES)
            self._zone.dnd_bind("<<Drop>>", self._on_drop)
        self._zone.bind("<Button-1>", lambda e: self._pick_file())
        self._zone_lbl.bind("<Button-1>", lambda e: self._pick_file())

        f_pli = ttk.LabelFrame(self.root, text="Pli")
        f_pli.pack(fill=tk.X, padx=16, pady=4)
        ttk.Radiobutton(
            f_pli,
            text="Bord court d’abord (haut/bas, puis gauche/droite)",
            variable=self._pli,
            value="bord-court",
        ).pack(anchor=tk.W, padx=8, pady=2)
        ttk.Radiobutton(
            f_pli,
            text="Bord long d’abord (gauche/droite, puis haut/bas)",
            variable=self._pli,
            value="bord-long",
        ).pack(anchor=tk.W, padx=8, pady=2)

        f_pad = ttk.LabelFrame(self.root, text="Pages")
        f_pad.pack(fill=tk.X, padx=16, pady=4)
        ttk.Checkbutton(
            f_pad,
            text="Compléter en multiple de 8 avec des pages blanches en fin de livret (si besoin)",
            variable=self._pad_blanks,
        ).pack(anchor=tk.W, padx=8, pady=4)
        self._pad_blanks.trace_add("write", self._on_pad_blanks_changed)

        ttk.Label(self.root, textvariable=self._status, foreground="#444").pack(**pad)

        row = ttk.Frame(self.root)
        row.pack(fill=tk.X, padx=16, pady=8)
        ttk.Button(row, text="Choisir un PDF…", command=self._pick_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="Imposer", command=self._impose_from_path_var).pack(side=tk.LEFT, padx=(0, 8))
        self._btn_finder = ttk.Button(row, text="Afficher dans le Finder", command=self._reveal, state=tk.DISABLED)
        if sys.platform == "darwin":
            self._btn_finder.pack(side=tk.LEFT)

        self._pending: Path | None = None

    def _on_pad_blanks_changed(self, *_args: object) -> None:
        if self._pending is not None:
            self._set_pending(self._pending)

    def _on_drop(self, event) -> None:
        paths = _parse_drop_paths(event.data)
        pdfs = [p for p in paths if p.suffix.lower() == ".pdf" and p.is_file()]
        if not pdfs:
            messagebox.showwarning("InQuarto", "Déposez un fichier PDF.")
            return
        self._set_pending(pdfs[0])

    def _pick_file(self) -> None:
        p = filedialog.askopenfilename(
            title="Choisir le PDF manuscrit",
            filetypes=[("PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
        )
        if p:
            self._set_pending(Path(p))

    def _set_pending(self, path: Path) -> None:
        pad = self._pad_blanks.get()
        errs, n = validate_manuscript_pdf(path, pad_blanks=pad)
        if errs:
            self._pending = None
            self._btn_finder.config(state=tk.DISABLED)
            self._last_out = None
            self._status.set("PDF refusé — voir la fenêtre d’erreur.")
            messagebox.showerror(
                "InQuarto — PDF non valide",
                "\n\n".join(errs),
            )
            return
        self._pending = path
        assert n is not None
        n_eff = padded_page_count(n) if pad else n
        k = k_from_page_count(n_eff)
        if pad and n_eff > n:
            self._status.set(
                f"OK — {path.name} ({n} p. + {n_eff - n} blanche(s) en fin → {n_eff} p., k={k}). Cliquez « Imposer »."
            )
        else:
            self._status.set(f"OK — {path.name} ({n} p., k={k}). Cliquez « Imposer ».")

    def _impose_from_path_var(self) -> None:
        if not self._pending:
            messagebox.showinfo("InQuarto", "Choisissez ou déposez d’abord un PDF.")
            return
        path = self._pending
        pad = self._pad_blanks.get()
        errs, _n = validate_manuscript_pdf(path, pad_blanks=pad)
        if errs:
            messagebox.showerror("InQuarto — PDF non valide", "\n\n".join(errs))
            return
        out = _default_output_path(path)
        try:
            k, n, n_imp = impose(
                path,
                out,
                pli_premier=self._pli.get(),
                pad_blanks=pad,
            )
        except ValueError as e:
            messagebox.showerror("InQuarto — erreur", str(e))
            self._status.set("Échec.")
            return
        except Exception as e:
            messagebox.showerror("InQuarto — erreur", f"{type(e).__name__} : {e}")
            self._status.set("Échec.")
            return

        self._last_out = out
        self._btn_finder.config(state=tk.NORMAL)
        self._status.set(f"Créé : {out.name}")
        pdf_pages = 2 * k
        blanc = ""
        if n_imp > n:
            blanc = f"\n\n({n_imp - n} page(s) blanche(s) ajoutée(s) en fin de livret pour l’imposition.)"
        messagebox.showinfo(
            "InQuarto",
            f"Fichier généré :\n{out}\n\n{pdf_pages} pages PDF = {k} feuilles A3 recto-verso ({n_imp} p. pour l’imposition)."
            + blanc,
        )

    def _reveal(self) -> None:
        if self._last_out and self._last_out.is_file():
            subprocess.run(["/usr/bin/open", "-R", str(self._last_out)], check=False)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if sys.platform != "darwin":
        # Tk fonctionne ailleurs ; le bouton Finder est macOS-only
        pass
    app = InQuartoApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
