# Drishti-AI — what every file does

Two halves that meet in the middle:

- **The research half** (`module1..4/`) trains and evaluates the models. Run by hand, produces checkpoints and metrics.
- **The product half** (`app/`, `dashboard/`) serves those checkpoints as a running application.

The product half never retrains anything. It loads what the research half produced and calls the same code, which is why served results match the paper exactly.

---

## The request path, end to end

What happens when someone drops a photo into the dashboard:

```
browser  ──►  Vite (4173)  ──►  Spring Boot (8080)  ──►  FastAPI (8000)  ──►  PyTorch/GPU
                 proxy            business logic          model serving        the model
                                        │
                                        ├──►  PostgreSQL (5432)     the record
                                        └──►  app/backend/data/     the image file
```

Each hop earns its place:

| Hop | Why it exists |
|---|---|
| Vite proxy | makes `/api` same-origin, so the browser needs no CORS |
| Spring Boot | auth, roles, thresholds, database, business rules |
| FastAPI | the only process holding PyTorch and the GPU |
| PostgreSQL | inspections, tools, forecasts, users, settings |

The split between Spring Boot and FastAPI is the important design choice. Re-implementing Module 4's feature engineering in Java would risk silently changing the forecast numbers. Keeping the ML in Python means the served model and the paper's model are the *same code*.

---

## Module 1 — defect detection (`module1_cv_defect/src/`)

The vision model: is this cast part good or defective?

### Core

| File | Does |
|---|---|
| `model.py` | Builds MobileNetV2. Loads ImageNet weights, replaces the 1000-class head with a 2-class one, freezes the backbone. `unfreeze_top_layers()` releases it for phase 2. |
| `dataset.py` | Loading and preprocessing. `build_transforms()` defines what the model sees — resize 224, flip, rotate; `strong=True` adds colour/affine/perspective for cameras unlike the dataset's rig. `get_train_val_test_loaders()` carves a validation split out of *train* so the test set stays untouched. |
| `train_proper.py` | **The trainer that produced the shipped model.** Two phases: head-only at lr 1e-3, then fine-tune at lr 1e-5. Keeps the best checkpoint by validation accuracy. |
| `infer.py` | `load_checkpoint()` — used by both the CLI and the live service. Also exports ONNX. |
| `evaluate.py` | Scores a checkpoint on the held-out test set. |

### Robustness

| File | Does |
|---|---|
| `ood.py` | Detects images the model was never trained on. Profiles the training set's 1280-d features and measures Mahalanobis distance at inference. Softmax cannot do this — random noise scores 0.999 confident. |
| `capture.py` | Collects new training data. Live camera view, `G`/`D` to label, writes straight into the ImageFolder layout. Works with a webcam or a phone over Wi-Fi. |

### Paper artefacts

`train.py` (superseded — selected on the test set), `train_baseline.py` (ResNet-50, SimpleCNN), `baselines.py`, `aggregate_results.py`, `benchmark_latency.py`, `gradcam.py` (Figure 4 saliency maps).

> `train.py` vs `train_proper.py`: the original chose its checkpoint by test accuracy, which optimistically biases the reported number. `train_proper.py` fixed that with a real validation split. The published 99.39% comes from the latter.

---

## Module 2 — vernacular alerts (`module2_vernacular_alert/`)

Turns a prediction into a sentence a shop-floor operator can act on.

| File | Does |
|---|---|
| `templates/alerts_hi.json` | The Hindi templates. One entry per defect code, plus `needs_review` (low confidence) and `not_recognised` (unfamiliar part). |
| `src/alerts.py` | Fills a template from a prediction. |
| `src/demo_pipeline.py` | CLI demo: image in, Hindi alert out. |

**This is the only module ported to Java** (`app/backend/.../alert/AlertService.java`). It reads the same JSON; the substitution is two fields, so a network hop bought nothing.

---

## Module 3 — predictive maintenance (`module3_predictive_maintenance/src/`)

How much life is left in this cutting tool?

| File | Does |
|---|---|
| `feature_extraction.py` | Raw vibration and current signals → 125 FFT/wavelet features per cycle. |
| `train.py` | XGBoost regressor for remaining useful life. Split **by physical tool**, so held-out numbers reflect real generalisation rather than memorised history. |
| `evaluate.py` | Per-tool metrics on the unseen test tools. |
| `streaming_replay.py` | Replays recorded readings as if live. The alert threshold and clipping here are mirrored exactly in the served path. |
| `baselines_pdm.py` | Constant-mean and linear baselines for context. |

---

## Module 4 — demand forecasting (`module4_demand_forecasting/src/`)

How much of each category will be needed next week?

| File | Does |
|---|---|
| `feature_extraction.py` | Raw Kaggle order log (~1.05M rows) → weekly totals per category. Also writes `weekly_category_demand.csv`, the history the forecaster seeds from. |
| `features.py` | **Single source of truth** for feature engineering — lags, rolling means, signed-log. Imported by training *and* serving so the two cannot drift. |
| `train.py` | Three XGBoost models: point forecast plus P10/P90 quantiles for the interval. |
| `forecast.py` | Recursive multi-step forecasting: predict a week, feed it back, repeat. |
| `evaluate.py`, `baselines_forecast.py`, `multiseed_m4.py` | Held-out WAPE, naive/seasonal/Prophet baselines, seed variance. |

---

## The inference service (`app/inference/`)

FastAPI. The only process that loads PyTorch and touches the GPU. Models load **once at startup**, not per request.

| File | Does |
|---|---|
| `main.py` | The HTTP endpoints. `/health`, `/predict/vision`, `/predict/maintenance`, `/predict/forecast`. |
| `paths.py` | Where every model file lives. One place to change. |
| `m1_vision.py` | Wraps Module 1. Calls `load_checkpoint` and `build_transforms` from the module itself, plus the OOD check. |
| `m3_maintenance.py` | Wraps Module 3. Same clipping and alert threshold as `streaming_replay.py`. |
| `m4_forecast.py` | Wraps Module 4. Reuses `compute_features` and `inverse_signed_log`. Reads history from the request, or from the recorded CSV. |

**The key idea:** these files put each module's `src/` on `sys.path` and import it. No model code is rewritten.

---

## The backend (`app/backend/src/main/java/com/drishti/`)

Spring Boot. Owns the database, auth, and every business rule.

### Auth (`auth/`)

| File | Does |
|---|---|
| `User.java`, `Role.java` | The account and its role — `OPERATOR` or `OWNER`. |
| `JwtService.java` | Issues and verifies tokens. 12-hour expiry. |
| `JwtAuthFilter.java` | Reads the bearer token on every request and sets the caller's role. |
| `AuthService.java` | Login and registration. BCrypt. Same error whether the username or password was wrong, so responses can't be used to discover accounts. |
| `AuthController.java` | `/api/auth/login`, `/register`, `/me`. |

### Inspection (`inspection/`)

| File | Does |
|---|---|
| `Inspection.java` | One row per inspected part: verdict, confidence, alert, image path, and the operator's correction. |
| `InspectionService.java` | **The business rules live here.** Calls the vision service, applies the threshold, decides pass/fail/review, saves the image, records feedback, computes KPIs. |
| `InspectionController.java` | `/api/inspections`, the image endpoint, `/api/kpis`. |

The verdict logic, in `decide()`:

1. Model doesn't recognise the image → **review** (whatever it guessed)
2. Model says defective → **fail**, always
3. Model says good but below the owner's threshold → **review**
4. Otherwise → **pass**

So the threshold can only ever make the system stricter. There is no setting that lets more defects through than the model alone would.

### The rest

| Package | Does |
|---|---|
| `maintenance/` | Tools, sensor readings, RUL predictions. |
| `forecast/` | Forecast points. Falls back to the recorded CSV when the database holds fewer than 52 weeks. |
| `settings/` | The thresholds. `GET` for anyone signed in, `PUT` for owners. |
| `ml/InferenceClient.java` | The HTTP client that calls the Python service. |
| `config/SecurityConfig.java` | Which routes need which role. Also the 401-vs-403 distinction. |
| `seed/EventsSeeder.java` | Loads `events.json` into the database on first run, including decoding the thumbnails to real files. |
| `seed/UserSeeder.java` | Creates the first accounts. Disabled with `SEED_USERS=false`. |

---

## The dashboard (`dashboard/src/`)

React + Vite.

| File | Does |
|---|---|
| `App.jsx` | Tabs, login gate, data loading. |
| `api.js` | Every API call. **Also adapts camelCase responses into the snake_case names the components already used**, which is why the charts never needed rewriting. |
| `auth.js` | The session. Token in localStorage, expiry handling, role checks. |

### Components

| File | Does |
|---|---|
| `Login.jsx` | Sign-in screen. |
| `Overview.jsx` | KPI tiles, recent inspections, tool status. |
| `LiveInspect.jsx` | **Drop a photo in, get a verdict.** The interactive demo. |
| `InspectionLog.jsx` | The full log, with the correct/wrong feedback buttons. |
| `FeedbackControl.jsx` | Stores the operator's true label — retraining data, not just agree/disagree. |
| `MaintenancePanel.jsx` / `RulChart.jsx` | Tool wear charts. |
| `InventoryForecast.jsx` / `ForecastChart.jsx` | Demand forecasts with P10–P90 bands. |
| `SettingsPanel.jsx` | Threshold sliders. Read-only for operators. |
| `AuthImage.jsx` | Images behind the token — a plain `<img src>` can't send an Authorization header, so it fetches the bytes and renders a blob URL. |
| `Benchmarks.jsx`, `RoiCalculator.jsx`, `StatusBadge.jsx`, `AnimatedNumber.jsx`, `Icons.jsx` | Supporting UI. |

`events.json` is no longer the data source, but it is still imported for **published model metrics** — benchmark tables, WAPE, test accuracy. Those are measured paper results, not runtime state.

---

## Scripts and docs at the root

| File | Does |
|---|---|
| `start-app.ps1` | Starts everything and opens a public URL. Reads the JWT secret from `app/secrets.local.json` — without it the app falls back to a signing key committed to this repo. |
| `stop-app.ps1` | Stops it all. Leaves PostgreSQL running. |
| `CAPTURE_SETUP.md` | How to collect real images at a shop. |
| `DEMO.md` | A recording script. |
| `APP_BUILD_PLAN.md` | The build plan and what's left. |
| `REPRODUCE.md` | How to reproduce every published number. |

---

## Two rules that hold the whole thing together

**1. Serving imports training code, never copies it.** `app/inference/` puts each module's `src/` on `sys.path`. If a preprocessing step changes, both change together. This is why the served model reproduces `proper_metrics_seed2.json` exactly and the forecast matches `events.json` to the decimal.

**2. Measured results are files, not live computation.** Benchmarks, WAPE and test accuracy come from the research half and are read, not recomputed. Recomputing them per request would let a demo quietly disagree with the paper.
