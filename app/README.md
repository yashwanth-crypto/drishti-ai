# Drishti-AI app

The prototype's models and dashboard, turned into a running multi-service application:
a **Spring Boot** backend owning the APIs and database, and a **FastAPI** service that
wraps the four validated model modules so the numbers can't drift from the paper.

```
React dashboard ──► Spring Boot :8080 ──► FastAPI :8000 ──► module1/3/4 models
                          │
                          └──► PostgreSQL :5432
```

## Running it

**1. PostgreSQL** runs as a Windows service (`postgresql-x64-16`) on the default
port 5432 and starts with the machine — nothing to do. To check it:

```bash
pg_isready -h localhost -p 5432
```

Then start the two application processes:

**2. Inference service** — loads the vision model on GPU and both XGBoost models at startup:

```bash
cd app/inference && ../../.venv/Scripts/python.exe -m uvicorn main:app --port 8000
```

**3. Backend** — creates its tables on first run and seeds them from `dashboard/src/data/events.json`:

```bash
cd app/backend && mvn spring-boot:run
```

Then `GET http://localhost:8080/actuator/health` should report `UP`.

**4. Dashboard** — proxies `/api` to the backend:

```bash
npm run dev --prefix dashboard
```

Open http://localhost:5173 and use the **Inspect a Part** tab to run a real image
through the model.

## Signing in

Two accounts are created on first run:

| Username | Password | Role |
|---|---|---|
| `owner` | `drishti-owner` | OWNER — everything, including thresholds and recompute |
| `operator` | `drishti-operator` | OPERATOR — inspect parts, read everything |

These are development credentials and the app logs a warning about them at
startup. Set `SEED_USERS=false` and register real accounts before deploying
anywhere that matters, and override `JWT_SECRET` (any real secret, 32+ bytes).

Every `/api` route except `/api/auth/login` and `/api/auth/register` needs a
bearer token:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/kpis
```

`401` means the token is missing or expired; `403` means the account is signed in
but its role isn't allowed. The dashboard treats these differently — only a 401
returns you to the login screen.

## API

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/auth/login` | `{username, password}` → JWT, valid 12h |
| `POST` | `/api/auth/register` | same, plus optional `role`; password min 8 chars |
| `GET` | `/api/auth/me` | who the current token belongs to |
| `GET` | `/api/settings` | thresholds — any signed-in user |
| `PUT` | `/api/settings` | **OWNER only** |
| `POST` | `/api/inspections` | multipart `image`, optional `partId` → runs the vision model, generates the Hindi alert, stores the row |
| `GET` | `/api/inspections?filter=all\|pass\|fail` | inspection log |
| `PATCH` | `/api/inspections/{id}/feedback` | `{"operatorVerdict": "ok_front"}` — records operator corrections |
| `GET` | `/api/kpis` | counts, pass rate, mean inference time |
| `GET` | `/api/maintenance/tools` | per-tool status with RUL history |
| `POST` | `/api/maintenance/predict` | `{toolRef, cycle, features}` — 125 named features |
| `GET` | `/api/forecast/categories` | every category's history + forward forecast |
| `POST` | `/api/forecast/run?category=X&horizon=4` | recomputes the forward forecast — **OWNER only** |

The inference service (internal; the backend is the only intended caller) exposes
`/predict/vision`, `/predict/maintenance`, `/predict/forecast`, plus
`/predict/maintenance/features` and `/predict/forecast/categories` to discover
what each model expects.

## Where the models come from

Nothing is retrained or reimplemented here. `app/inference` puts each module's
`src/` on `sys.path` and calls the existing code:

- **Vision** — `module1_cv_defect/src/infer.py`'s `load_checkpoint`, with the same
  `build_transforms(224, train=False)` preprocessing. Loads once at startup rather
  than per call.
- **Maintenance** — the same `XGBRegressor.load_model` + clip-to-[0,1] as
  `streaming_replay.py`, reusing its `WEAR_ALERT_THRESHOLD`.
- **Forecast** — `module4_demand_forecasting/src/features.py`'s `compute_features`
  and `inverse_signed_log`, so served features match trained features exactly.
- **Alerts** — Module 2 is the one thing ported to Java (`alert/AlertService.java`).
  It reads the same `templates/alerts_hi.json`; the substitution is two fields, so
  a network hop would buy nothing.

## Verified against the prototype

The served models reproduce the recorded results exactly — the point of keeping
inference in Python rather than reimplementing it:

| Module | Check | Result |
|---|---|---|
| M1 vision | full 715-image held-out test set through `POST /predict/vision` | **99.30%**, confusion `[[450,3],[2,260]]` — identical to `proper_metrics_seed2.json`, the shipped checkpoint |
| M4 forecast | `Category_019` 4-week horizon through `POST /api/forecast/run` | point and P10/P90 match `events.json` to the decimal on all 4 weeks |

The paper's headline 99.39% ± 0.24 is the mean across seeds 42/1/2; the deployed
checkpoint is the seed-2 run at 99.30%.

## Known gaps

- **Forecast history lives outside the database.** Module 4's features include a
  52-week lag, but the seeded series only carries 16 weeks per category, so
  `POST /api/forecast/run` forecasts from `module4_demand_forecasting/data/weekly_category_demand.csv`
  (271 weeks) instead. That file is gitignored; rebuild it with
  `python src/feature_extraction.py` after downloading the raw demand dataset.
  Verified to reproduce the prototype's published figures exactly.
- **The defect threshold is stored but not yet applied.** An owner can set it and
  it persists, but the inspection service doesn't consult it when deciding
  pass/fail. Wiring that in is what actually delivers §9.2.
- **No operator feedback UI.** `PATCH /api/inspections/{id}/feedback` works, but
  nothing in the dashboard calls it yet.
- **Not containerized.** Docker Compose needs WSL2 on this machine.
- **Module 3 has no source data locally.** The milling dataset isn't downloaded, so
  `POST /api/maintenance/predict` only works when the caller supplies all 125
  features. Fetch the list from `GET /predict/maintenance/features`.
