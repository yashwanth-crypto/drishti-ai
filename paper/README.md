# Drishti-AI — Overleaf paper package

A complete, written paper in **normal single-column article format (12pt)** —
larger, readable text (not IEEE two-column). All sections have full prose, and
every table/figure is placed in order right where it is discussed.

## Contents
- `main.tex` — the full paper (`\documentclass[12pt]{article}`). Compiles with
  **pdfLaTeX** alone; the bibliography is embedded (no BibTeX run needed).
- `refs.bib` — optional BibTeX version of the 48 references (only if you switch
  to `\bibliography{refs}`).
- `figures/` — all 15 images, including your real architecture diagram as
  `fig01_architecture_author.png` (Figure 1).

## Compile on Overleaf
1. New Project -> Upload Project -> select the zip (or upload this folder).
2. Menu -> Compiler -> **pdfLaTeX**.
3. Recompile.

## Notes
- Citations are shown as bracketed numbers `[n]` matching the reference list
  order (screenshot style). To get auto-numbered hyperlinked citations later,
  replace each literal `[n]` with `\cite{key}` (keys are in `refs.bib`) and use
  `\bibliography{refs}` with `\bibliographystyle{ieeetr}` or `plain`.
- Figures use `[H]` (exact placement) so nothing floats out of order. If a page
  looks sparse, that is the trade-off for strict ordering; switch `[H]` to `[ht]`
  to let LaTeX optimize spacing.
- Reference **[42]** (`piecuch2025milling`) still needs its real publisher/DOI.
- Section prose is a first draft — edit freely.
