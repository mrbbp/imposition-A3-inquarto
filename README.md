# Imposition in quarto — **8×k** pages → **k** feuilles A3 (imbriqué)

## Contexte

- **Entrée** : PDF **143,5 × 205 mm** par page (fonds perdus compris), nombre de pages **multiple de 8**, **≥ 8** (ou **`--pad-blanks`** / case GUI pour compléter avec des **pages blanches en fin de livret**). Le script **déduit** **k = pages / 8** (feuilles A3). Les tables d’imposition sont **générées** par l’algorithme (`layouts_dynamic.py`), pas des fichiers séparés par taille.
- **Sortie** : **2×k pages PDF** = **k** feuilles A3 recto-verso (2×2 pages manuscrit par face).
- **Atelier** : plier **chaque** A3 **deux fois** (in quarto) → **k** petits cahiers ; **imbriquer** ; **2 agrafes** au milieu du dos ; **rogner la tête**.

Exemples : 8 p. → k=1 ; 16 p. → k=2 ; 24 → k=3 ; 32 → k=4 ; 40 → k=5 ; etc.

### Contrôle sur la feuille 1 (recto) — cas **32 p. (k=4)**

En partant du **bas à droite**, ordre **BR → BL → TL → TR** : tu dois voir **1, 32, 29, 4** (comme sur ta maquette). Si ce n’est pas le cas, le PDF ne correspond pas au pli prévu.

**Verso feuille 1** : **TL=3, TR=30, BL=2, BR=31** ; **TL et TR** en rotation 180° dans le PDF, **BL et BR** à 0°.

### Ordre des plis (A3 portrait)

Par défaut, le PDF est calibré pour un pli **facile** :

1. **1er pli — bords courts** : rabattre **le haut sur le bas** (pli **horizontal**, tu divises la **hauteur** 420 mm).
2. **2e pli — bords longs** : rabattre **gauche sur droite** (pli **vertical**, tu divises la **largeur** 297 mm).

Si tu plies plutôt **d’abord gauche/droite**, puis **haut/bas**, régénère avec :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py --pli-premier bord-long "livret SABY.pdf" "sortie.pdf"
```

## Arborescence

- **À la racine du dossier projet** (`…/inquarto/`) : surtout **`Imposer.command`** (double-clic) et ce `README`. Tu y déposes les PDF à traiter en lot.
- **Dossier caché** **`.inquarto/`** : scripts Python, `requirements.txt`, venv (`.inquarto/.venv`), lanceur GUI interne.

## Installation

**Recommandé** : double-clic sur **`Imposer.command`**. Il crée **`.inquarto/.venv`** si besoin et installe **`requirements.txt`** si `import fitz` échoue.

Manuellement (même résultat) :

```bash
cd "/Users/ericchoisy-bernard/Sites/DNMADE-2526/inquarto"
/usr/bin/python3 -m venv .inquarto/.venv
.inquarto/.venv/bin/pip install -r .inquarto/requirements.txt
```

**Interface graphique et Tk** : si `python3` vient de **Homebrew** sans Tcl/Tk, `import tkinter` peut échouer (`No module named '_tkinter'`). Recrée le venv avec le **Python système** puis réinstalle les paquets :

```bash
rm -rf .inquarto/.venv
/usr/bin/python3 -m venv .inquarto/.venv
.inquarto/.venv/bin/pip install -r .inquarto/requirements.txt
```

Ou installe Tk pour ta version Homebrew (ex. `brew install python-tk@3.14` si disponible).

## Interface graphique (macOS)

- **`Imposer.command`** (racine du projet) : double-clic — lance **`impose_quarto.py` sans argument** ; les **`*.pdf`** recherchés sont ceux **du même dossier que `Imposer.command`** (pas dans `.inquarto/`), hors `*_impose_A3.pdf`. Le venv **`.inquarto/.venv`** est créé / alimenté automatiquement si besoin.
- **`Lancer InQuarto GUI.command`** : dans **`.inquarto/`** (Finder : *Aller* → *Aller au dossier…* → `.inquarto`). Même logique de venv / `pip install` automatique.
- Terminal : `.inquarto/.venv/bin/python .inquarto/impose_quarto.py` ou `.inquarto/.venv/bin/python .inquarto/in_quarto_gui.py`.

**Glisser-déposer** un PDF sur la zone grise (nécessite **`tkinterdnd2`**, inclus dans `requirements.txt`). Sans cette lib, **clique** sur la zone pour choisir un fichier.

**Contrôles automatiques** avant imposition :

- **32 pages** exactement ;
- **A5 portrait** (~148×210 mm par page, tolérance ~8 %) ;
- rejet si **paysage** ou dimensions trop éloignées.

Sortie : même dossier que le source, fichier `nom_impose_A3.pdf`. Après succès, **Afficher dans le Finder** (macOS) ouvre le dossier sur le fichier généré.

## Usage (ligne de commande)

Imposer un manuscrit :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py "livret SABY.pdf" "livret SABY_impose_A3.pdf"
```

**Pages blanches en fin de livret** : si le nombre de pages n’est pas un multiple de 8, **`--pad-blanks`** ajoute le nombre de pages blanches nécessaire **à la fin** (le PDF source n’est pas modifié ; tout se fait en mémoire).

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py --pad-blanks "livret.pdf" "livret_impose_A3.pdf"
```

Le **batch** (double-clic sur **`Imposer.command`**) passe **`--pad-blanks` par défaut** (complément automatique si besoin). Pour **exiger** un multiple de 8 sans complément : **`INQUARTO_STRICT_PAGES=1`**. L’**interface graphique** propose une case **« Compléter en multiple de 8… »**.

Sortie implicite (même dossier que le manuscrit) :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py "livret SABY.pdf"
```

Sans argument : le script **liste les `*.pdf`** **un niveau au-dessus de `.inquarto`** (donc le dossier qui contient **`Imposer.command`**), non récursif, et impose chacun vers `nom_impose_A3.pdf` (les `*_impose_A3.pdf` sont ignorés).

```bash
cd "/Users/ericchoisy-bernard/Sites/DNMADE-2526/inquarto"
.inquarto/.venv/bin/python .inquarto/impose_quarto.py
```

**Ferrage vers le centre (défaut)** : même échelle qu’avant, mais chaque page est ferrée **vers la croix au centre de la face A3** : colonne gauche → droite, droite → gauche, rangée du haut → bas, rangée du bas → haut. Ça supprime le blanc aux **jonctions verticales et horizontales** entre demi-pages (doubles pages côte à côte ou l’une au-dessus de l’autre). Désactiver : **`--no-gutter-align`** sur la ligne de commande.

PDF **léger** pour suivre les maquettes (32 p., même pipeline) :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py "DN1 - livret saby_test.pdf" "DN1 - livret saby_test_impose_A3.pdf"
```

Épreuve (manuscrit généré avec gros numéros + « haut ↑ »), puis imposition :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py --proof-output "test_impose_A3.pdf"
```

Générer seulement le manuscrit épreuve :

```bash
.inquarto/.venv/bin/python .inquarto/impose_quarto.py --proof-only "manuscrit_epreuve_32.pdf"
```

## Impression

- **Recto-verso**, retournement sur le **bord long** (souvent « retournement sur le bord long » / *flip on long edge*).
- Ordre des pages PDF : feuille 1 recto, feuille 1 verso, feuille 2 recto, … — à enchaîner en duplex sans réordonner si l’imprimante suit la séquence fichier.

Si le verso est décalé ou inversé, tester l’autre option de retournement dans le pilote. Si les numéros de l’épreuve restent faux après un pli soigné, essaie `--pli-premier bord-long` ou adapte la logique dans **`.inquarto/layouts_dynamic.py`** (génération des tables).

## Imbriquement des cahiers

Après pli quarto de chaque feuille A3 :

1. **Cahier feuille k** (paires centrales du livre) — le plus petit bloc.
2. Glisser dedans **feuille k−1**, puis … jusqu’à **feuille 1** (couverture / fin de livre à l’extérieur).

Vérifier avec l’épreuve numérotée avant tirage définitif.

## Fichiers

| Fichier | Rôle |
|--------|------|
| **`Imposer.command`** | Racine projet : double-clic, batch PDF du dossier parent |
| `README.md` | Cette documentation |
| `.inquarto/layouts_dynamic.py` | Génération algorithmique des tables (pages + rotations) |
| `.inquarto/impose_quarto.py` | CLI PyMuPDF + `validate_manuscript_pdf()` |
| `.inquarto/in_quarto_gui.py` | Appli Tk glisser-déposer |
| `.inquarto/Lancer InQuarto GUI.command` | Double-clic GUI (macOS) |
| `.inquarto/requirements.txt` | `pymupdf`, `tkinterdnd2` |

Pour ajuster l’ordre ou les rotations après un test papier, modifier **`.inquarto/layouts_dynamic.py`** (ou le modèle physique si la formule doit changer).
