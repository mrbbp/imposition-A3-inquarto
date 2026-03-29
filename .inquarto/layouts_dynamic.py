"""
Imposition in quarto imbriqué — **génération algorithmique** des tables.

Pour un manuscrit de **T** pages (**T** multiple de 8, **T ≥ 8**), on pose **k = T / 8**
feuilles A3. Complément des paires vis-à-vis de la lecture : **T + 1** (comme 33 pour 32 p.).

- **Feuilles « extérieures »** (indices **s = 0 … k−2**) : chaque feuille juxtapose un bloc
  **bas** (pages **4s+1 … 4s+4**) et un bloc **haut** (pages **T−4s−3 … T−4s**).
- **Feuille centrale** (toujours la dernière) : les **8** pages consécutives
  **4(k−1)+1 … 4k** (pour **k = 1**, une seule feuille = ce bloc, pages **1 … 8**).

Grille (portrait A3, origine haut-gauche) :

        col0    col1
row0   TL      TR
row1   BL      BR

**Pli bord long d’abord** : échange des deux rangées sur chaque face (comme avant).
"""

from __future__ import annotations

from typing import List, Tuple

Cell = Tuple[int, int]
Face = List[List[Cell]]
Sheet = dict[str, Face]


def _swap_rows_face(face: Face) -> Face:
    return [list(face[1]), list(face[0])]


def _outer_sheet(s: int, T: int) -> Sheet:
    """
    Feuille « paire début / fin » numéro s (0 ≤ s ≤ k−2).
    Paires en somme T+1 entre les deux blocs.
    """
    return {
        "front": [
            [(T - 4 * s - 3, 180), (4 * s + 4, 180)],
            [(T - 4 * s, 0), (4 * s + 1, 0)],
        ],
        "back": [
            [(4 * s + 3, 180), (T - 4 * s - 2, 180)],
            [(4 * s + 2, 0), (T - 4 * s - 1, 0)],
        ],
    }


def _center_sheet(first_page: int) -> Sheet:
    """
    Feuille avec 8 pages consécutives : first_page … first_page+7.
    (first_page = 4(k−1)+1 pour la dernière feuille d’un livret à k feuilles.)
    """
    a = first_page
    return {
        "front": [
            [(a + 4, 180), (a + 3, 180)],
            [(a + 7, 0), (a, 0)],
        ],
        "back": [
            [(a + 2, 180), (a + 5, 180)],
            [(a + 1, 0), (a + 6, 0)],
        ],
    }


def generate_sheets_bord_court(total_pages: int) -> List[Sheet]:
    """Lève ValueError si total_pages n'est pas un multiple de 8 ≥ 8."""
    T = total_pages
    if T < 8 or T % 8 != 0:
        raise ValueError(f"Nombre de pages attendu : multiple de 8 ≥ 8 (reçu {T}).")
    k = T // 8
    sheets: List[Sheet] = []
    if k == 1:
        sheets.append(_center_sheet(1))
    else:
        for s in range(k - 1):
            sheets.append(_outer_sheet(s, T))
        sheets.append(_center_sheet(4 * (k - 1) + 1))
    return sheets


def generate_sheets_bord_long(total_pages: int) -> List[Sheet]:
    bc = generate_sheets_bord_court(total_pages)
    return [
        {
            "front": _swap_rows_face(s["front"]),
            "back": _swap_rows_face(s["back"]),
        }
        for s in bc
    ]


def _regression_matches_legacy_32() -> bool:
    """Contrôle que la génération pour 32 p. coïncide avec l’ancienne table figée."""
    g = generate_sheets_bord_court(32)
    legacy = [
        {
            "front": [
                [(29, 180), (4, 180)],
                [(32, 0), (1, 0)],
            ],
            "back": [
                [(3, 180), (30, 180)],
                [(2, 0), (31, 0)],
            ],
        },
        {
            "front": [
                [(25, 180), (8, 180)],
                [(28, 0), (5, 0)],
            ],
            "back": [
                [(7, 180), (26, 180)],
                [(6, 0), (27, 0)],
            ],
        },
        {
            "front": [
                [(21, 180), (12, 180)],
                [(24, 0), (9, 0)],
            ],
            "back": [
                [(11, 180), (22, 180)],
                [(10, 0), (23, 0)],
            ],
        },
        {
            "front": [
                [(17, 180), (16, 180)],
                [(20, 0), (13, 0)],
            ],
            "back": [
                [(15, 180), (18, 180)],
                [(14, 0), (19, 0)],
            ],
        },
    ]
    return g == legacy


if __name__ == "__main__":
    assert _regression_matches_legacy_32(), "Régression 32 p."
    assert len(generate_sheets_bord_court(8)) == 1
    assert len(generate_sheets_bord_court(16)) == 2
    print("layouts_dynamic OK (32 p. = legacy, k=1 et k=2).")
