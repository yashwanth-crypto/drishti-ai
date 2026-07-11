# Drishti-AI

An offline, four-part AI system for small manufacturers (MSMEs): defect detection,
a Hindi shop-floor alert, tool-wear prediction, and demand forecasting — all running
on an ordinary CPU with no cloud, reporting to one dashboard.

**Live dashboard:** https://<your-username>.github.io/<repo-name>/
*(replace with your URL once GitHub Pages is enabled — see below)*

---

## What it does

| Module | Task | Model | Headline result |
|---|---|---|---|
| M1 | Casting surface-defect detection | MobileNetV2 (transfer) | 99.39% ± 0.24 test accuracy; 2.37 ms/image on CPU |
| M2 | Hindi operator alert | Rule-mapped templates | one plain-language alert per inspection |
| M3 | Tool remaining-useful-life | XGBoost | R² = 0.545 on tools held out of training |
| M4 | Weekly demand forecast | XGBoost + quantile intervals | 19.7% WAPE, beats naïve/seasonal/Prophet |

All numbers come from public datasets under held-out tests, not a live factory. See
the paper in [`paper/`](paper/) and the honest caveats in [`PAPER_RESULTS.md`](PAPER_RESULTS.md).

## Repository layout

```
dashboard/                     React + Vite dashboard (the live site)
module1_cv_defect/             CV defect detection (training, ONNX export, Grad-CAM)
module2_vernacular_alert/      Hindi alert generation
module3_predictive_maintenance/ tool-wear regression
module4_demand_forecasting/    demand forecasting
paper/                         LaTeX paper (main.tex, refs.bib, figures)
paper_figures/                 generated result figures
make_paper_figures.py          regenerates all figures from saved results
requirements.txt               Python dependencies
REPRODUCE.md                   commands + dataset download links
```

## Run the dashboard locally

```bash
cd dashboard
npm install
npm run dev        # open http://localhost:5173
```

The dashboard is self-contained: it reads bundled results from
`dashboard/src/data/events.json`, so it needs no backend.

## Deploy the dashboard on GitHub Pages

A workflow at [`.github/workflows/deploy-dashboard.yml`](.github/workflows/deploy-dashboard.yml)
builds and publishes the dashboard on every push to `main`. To turn it on:

1. Push this repo to GitHub.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. Push to `main` (or run the workflow manually). The site appears at
   `https://<your-username>.github.io/<repo-name>/`.

## Reproduce the models

The raw datasets are public and **not** stored in this repo (they are large). Download
links and the exact training commands are in [`REPRODUCE.md`](REPRODUCE.md). Trained
result metadata (metrics JSONs) and the ONNX defect model are included so the dashboard
and figures work without retraining.

## Note

This is a reproducible proof of concept, not a shipped product. It has not been piloted
in a real factory.
