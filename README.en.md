[中文](README.md) · **English** · [Français](README.fr.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

# 18xx Rulebook Chinese Translation · Workflow and Deliverables

> A Chinese translation of 18xx (railway management board game) rulebooks that takes **the English original rules as the sole authority**, plus typeset edition PDFs that "reproduce the original book's layout and embed the original illustrations in their corresponding positions".
> The goal is not fluency but **being able to trace every clause back to the English original with the Chinese text in hand**: heading numbers, terminology and clause page numbers are all traceable.

**Repository version: v1.0.0** (2026-10-25)

**Current versions**

| Component | Version | Notes |
|:--|:--|:--|
| skill `18xx-translation` | **v1.0.0** | Two-step delivery: content source md → typeset edition PDF in the original layout |
| Deliverables | — | 2 rulebook Chinese translations (typeset editions included) + 1 solo mode + 2 question-and-answer documents + glossary/rules overview |

---

## 1. Deliverables

| Title | Chinese content source | Typeset edition PDF | Pages | Size | Version |
|:--|:--|:--|--:|--:|:--|
| **Railways of the Lost Atlas** (2nd Ed.) | [md](<works/Railways/Railways_规则中文翻译.md>) | [PDF](<works/Railways/Railways_规则中文翻译（排版版）.pdf>) | 44 | 22.4 MB | Content v1.2 · Typeset v1.1 |
| 　└ Solo mode rules | [md](<works/Railways/Railways_单人模式规则中文翻译.md>) | On demand | — | — | v1.0 |
| 　└ Questions and answers | [md](<works/Railways/Railways_疑惑与答疑.md>) | — | — | — | 2026-10-03 |
| **1880 China** (Lookout 2022) | [md](<works/1880China/1880China_规则中文翻译.md>) | [PDF](<works/1880China/1880China_规则中文翻译（排版版）.pdf>) | 36 | 17.9 MB | Content v1.1 · Typeset v1.0 |
| 　└ Questions and answers | [md](<works/1880China/1880China疑惑与答疑.md>) | — | — | — | 2026-09-23 |

### Reference material

| File | Purpose |
|:--|:--|
| [18XX_中英术语对照表.md](<works/glossary/18XX_中英术语对照表.md>) | Cross-title terminology rulings (including terms that are easy to mistranslate and records of errors in the official Chinese translation) |
| [18XX_规则总览.md](<works/glossary/18XX_规则总览.md>) | Series rules framework based on 1830, for quick rules lookup |

### Key parameters of the two titles (basis for the reproduction)

| Title | Original trim size | Paper colour | Layout | Illustrations |
|:--|:--|:--|:--|:--|
| Railways 2nd | 285×214 mm landscape | `#FFF8ED` | Two-column magazine style: side-note boxes/caption boxes/company colour cards/full-width tables | Figures 1–9, component anatomy, tabletop setup, all company emblems |
| 1880 China | A4 595×842 pt portrait | `#EDE8E0` | Two columns; corporation table with certificate colour blocks; emblem set into the heading | Diagrams from the original book, component images, company emblems |

---

## 2. How to use

### 2.1 Looking up rules

- The heading numbers in each md match the English original book, and every section heading is followed by the **printed page number in the original book**;
- The glossary gives four columns: "English — recommended rendering — wording actually used in existing Chinese translations — notes"; where they conflict, the English prevails;
- Every question-and-answer entry gives **the rules clause + playtest/derivation + a game or page you can check**.

### 2.2 Installing the skill

Copy `skills/18xx-translation` into the agent's skills directory (`~/.claude/skills/`, `~/.agents/skills/` or `~/.dsh/skills/`). It ships with:

- `references/中译排版PDF.md` — the complete typesetting manual (pipeline, parse hooks, the three illustration anchors, the three boundary pitfalls, pymupdf post-processing, part banners/side colour tabs, bound-volume conventions);
- `assets/build_railways_pdf.py`, `assets/clip_railways_art.py` — landscape 1:1 sample;
- `assets/build_1880china_pdf.py`, `assets/clip_1880china_art.py` — A4 portrait sample;
- `references/启动提示词.md` — a kickoff prompt you can paste as is.

### 2.3 Two-step delivery

1. **Content source** `<作品>_规则中文翻译.md`: paragraph-by-paragraph comparison against the English original rules, with no abridging/expansion/fabrication; terminology rulings (Appendix A), errata in the original book (Appendix B), verification records (Appendix C).
2. **Typeset edition** `<作品>_规则中文翻译（排版版）.pdf`: md is the sole content source; the original trim size/paper colour/two columns are reproduced and the original illustrations are embedded at their corresponding positions; not a word of the body text is changed.

---

## 3. Versions and releases

- Repository tag: `v1.0.0` (first release, 2026-10-25).
- **Two version tracks**: the content edition (Chinese translation vX.Y) and the typeset edition (vX.Y) keep separate histories; the PDF cover, footer and metadata agree in all three places.
- Fixed before this release: the Railways typeset edition metadata was still at v1.0 (the cover/footer were already v1.1) and the file has been regenerated; in 7 18xx documents the acknowledgements and attribution were changed from "analysis report wording" to "translation/compilation wording".
- Only translations and typeset files are published; the English original PDFs, scans and game assets are not.

---

## 4. Copyright and usage notice

- **Copyright in the original text** belongs to the original publishers and designers: Railways of the Lost Atlas © Asterisk Games (Jacob Schacht, Kevin Delger); 1880 China © Lookout GmbH (design: Helmut Ohley / Leonhard Orgler, as stated on the copyright page of the original book).
- **The Chinese translation, typesetting and terminology work** are the labour of **Pig9013**; **when reposting, credit the author and the source; commercial use is prohibited**.
- For study and play discussion only; not for commercial publication or paid distribution.
- If a rights holder considers any content inappropriate, please contact us through a GitHub Issue; it will be taken down immediately.

---

## 5. Acknowledgements

- The original publishers, designers and artists of Railways and 1880;
- The [18xx.games](https://18xx.games/) community — terminology and difficult clauses drew on games and discussions on the site;
- Existing rulebook translations in the Chinese 18xx community (used for wording comparison; where they conflict, the English original always prevails).

---

## 6. Repository structure

`@
skills/18xx-translation/   SKILL.md + references/ + assets/
works/Railways/            md + typeset edition PDF + solo mode + questions and answers
works/1880China/           md + typeset edition PDF + questions and answers
works/glossary/            Chinese-English glossary + rules overview
tools/verify_repo.py       static self-check before release
`@

---

*Translation: Pig9013 ｜ Model: Deepseek-flash ｜ Last updated: 2026-10-25*
