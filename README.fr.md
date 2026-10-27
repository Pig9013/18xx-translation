[中文](README.md) · [English](README.en.md) · **Français** · [日本語](README.ja.md) · [Русский](README.ru.md)

# Traduction chinoise des livres de règles 18xx · Flux de travail et livrables

> Traduction chinoise des livres de règles 18xx (jeu de gestion ferroviaire) fondée sur **l'original anglais comme unique autorité**, ainsi que des PDF en édition composée qui « reproduisent la mise en page de l'ouvrage d'origine et insèrent les illustrations originales à leur emplacement ».
> Le but n'est pas la fluidité, mais de **pouvoir vérifier chaque clause dans l'original anglais, texte chinois en main** : numéros de titres, terminologie et numéros de page des clauses sont tous traçables.

**Version du dépôt : v1.0.0** (2026-10-25)

**Versions actuelles**

| Composant | Version | Description |
|:--|:--|:--|
| skill `18xx-translation` | **v1.0.0** | Livraison en deux temps : source md → PDF en édition composée à la mise en page d'origine |
| Livrables | — | 2 traductions chinoises de livres de règles (édition composée incluse) + 1 mode solo + 2 documents de questions-réponses + glossaire/aperçu des règles |

---

## 1. Livrables

| Ouvrage | Source du contenu chinois | PDF en édition composée | Pages | Taille | Version |
|:--|:--|:--|--:|--:|:--|
| **Railways of the Lost Atlas** (2e éd.) | [md](<works/Railways/Railways_规则中文翻译.md>) | [PDF](<works/Railways/Railways_规则中文翻译（排版版）.pdf>) | 44 | 22.4 MB | Contenu v1.2 · Composition v1.1 |
| 　└ Règles du mode solo | [md](<works/Railways/Railways_单人模式规则中文翻译.md>) | Sur demande | — | — | v1.0 |
| 　└ Questions et réponses | [md](<works/Railways/Railways_疑惑与答疑.md>) | — | — | — | 2026-10-03 |
| **1880 China** (Lookout 2022) | [md](<works/1880China/1880China_规则中文翻译.md>) | [PDF](<works/1880China/1880China_规则中文翻译（排版版）.pdf>) | 36 | 17.9 MB | Contenu v1.1 · Composition v1.0 |
| 　└ Questions et réponses | [md](<works/1880China/1880China疑惑与答疑.md>) | — | — | — | 2026-09-23 |

### Documents de référence

| Fichier | Usage |
|:--|:--|
| [18XX_中英术语对照表.md](<works/glossary/18XX_中英术语对照表.md>) | Arbitrages terminologiques transversaux (termes faciles à mal traduire, relevé des erreurs de la traduction chinoise officielle) |
| [18XX_规则总览.md](<works/glossary/18XX_规则总览.md>) | Cadre de règles de la série fondé sur 1830, pour une consultation rapide |

### Paramètres clés des deux ouvrages (base de la reproduction)

| Ouvrage | Format de l'édition d'origine | Couleur du papier | Mise en page | Illustrations |
|:--|:--|:--|:--|:--|
| Railways 2nd | 285×214 mm à l'italienne | `#FFF8ED` | Deux colonnes façon magazine : encadrés de notes/encadrés de légendes/cartes de couleur des compagnies/tableaux pleine largeur | Figures 1–9, anatomie des composants, disposition sur la table, tous les emblèmes des compagnies |
| 1880 China | A4 595×842 pt portrait | `#EDE8E0` | Deux colonnes ; tableau des corporations avec blocs de couleur des certificats ; emblème inséré dans le titre | Schémas de l'ouvrage d'origine, images des composants, emblèmes des compagnies |

---

## 2. Utilisation

### 2.1 Consultation des règles

- Les numéros de titres de chaque md correspondent à ceux de l'ouvrage anglais d'origine, et chaque titre de section est suivi du **numéro de page imprimée de l'ouvrage d'origine** ;
- Le glossaire comporte quatre colonnes : « anglais — traduction recommandée — formulation réellement employée dans les traductions chinoises existantes — remarques » ; en cas de conflit, l'anglais fait foi ;
- Chaque entrée de questions-réponses donne **la clause de règle + l'essai en partie/la déduction + une partie ou une page d'origine à consulter**.

### 2.2 Installation du skill

Copier `skills/18xx-translation` dans le répertoire skills de l'agent (`~/.claude/skills/`, `~/.agents/skills/` ou `~/.dsh/skills/`). Il contient :

- `references/中译排版PDF.md` — le manuel de composition complet (chaîne de production, hooks d'analyse, trois ancrages des illustrations, trois pièges de bord, post-traitement pymupdf, bandeaux de partie/onglets de couleur latéraux, conventions du volume relié) ;
- `assets/build_railways_pdf.py`, `assets/clip_railways_art.py` — modèle 1:1 à l'italienne ;
- `assets/build_1880china_pdf.py`, `assets/clip_1880china_art.py` — modèle A4 portrait ;
- `references/启动提示词.md` — prompt de démarrage à coller tel quel.

### 2.3 Livraison en deux temps

1. **Source du contenu** `<作品>_规则中文翻译.md` : confrontation paragraphe par paragraphe avec l'original anglais, sans abréger/développer/inventer ; arbitrages terminologiques (annexe A), errata de l'ouvrage d'origine (annexe B), relevé des vérifications (annexe C).
2. **Édition composée** `<作品>_规则中文翻译（排版版）.pdf` : le md est l'unique source du contenu ; le format, la couleur du papier et les deux colonnes de l'ouvrage d'origine sont reproduits et les illustrations originales insérées à leur emplacement ; pas un mot du corps de texte n'est modifié.

---

## 3. Versions et publication

- Tag du dépôt : `v1.0.0` (première publication, 2026-10-25).
- **Double suivi de version** : l'édition de contenu (traduction chinoise vX.Y) et l'édition composée (vX.Y) ont chacune leur historique ; la couverture, le pied de page et les métadonnées du PDF concordent.
- Corrections apportées avant cette publication : les métadonnées de l'édition composée Railways étaient restées en v1.0 (couverture/pied de page déjà en v1.1) et le fichier a été régénéré ; dans 7 documents 18xx, les remerciements et la signature sont passés du « registre du rapport d'analyse » au « registre de la traduction/compilation ».
- Seules les traductions et les compositions sont publiées ; les PDF anglais d'origine, les scans et les éléments de jeu ne le sont pas.

---

## 4. Droits d'auteur et conditions d'utilisation

- **Les droits sur le texte original** appartiennent aux éditeurs et aux auteurs d'origine : Railways of the Lost Atlas © Asterisk Games (Jacob Schacht, Kevin Delger) ; 1880 China © Lookout GmbH (conception : Helmut Ohley / Leonhard Orgler, selon la page de copyright de l'ouvrage).
- **La traduction chinoise, la composition et le travail terminologique** sont le fruit du travail de **Pig9013** ; **en cas de republication, citez l'auteur et la source ; usage commercial interdit**.
- Pour l'étude et les échanges autour du jeu uniquement ; ni édition commerciale ni diffusion payante.
- Si un ayant droit juge un contenu inapproprié, qu'il nous contacte via une GitHub Issue : le contenu sera retiré immédiatement.

---

## 5. Remerciements

- Aux éditeurs, auteurs et illustrateurs d'origine de Railways et de 1880 ;
- À la communauté [18xx.games](https://18xx.games/) — la terminologie et les clauses difficiles s'appuient sur les parties et les discussions du site ;
- Aux traductions de règles existantes dans la communauté 18xx chinoise (utilisées pour comparer les formulations ; en cas de conflit, l'original anglais fait toujours foi).

---

## 6. Structure du dépôt

`@
skills/18xx-translation/   SKILL.md + references/ + assets/
works/Railways/            md + PDF en édition composée + mode solo + questions-réponses
works/1880China/           md + PDF en édition composée + questions-réponses
works/glossary/            glossaire chinois-anglais + aperçu des règles
tools/verify_repo.py       autocontrôle statique avant publication
`@

---

*Traduction : Pig9013 ｜ Modèle : Deepseek-flash ｜ Dernière mise à jour : 2026-10-25*
