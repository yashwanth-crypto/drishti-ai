# Drishti-AI dashboard

React + Vite front end for the Drishti-AI platform. It reads live data from the
Spring Boot backend (see [`../app`](../app)) — inspections, KPIs, tool wear and
demand forecasts all come from the API, not a checked-in JSON file.

## Running

The backend (`:8080`) and inference service (`:8000`) need to be up first — see
[`../app/README.md`](../app/README.md). Then:

```bash
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8080`, so the browser stays same-origin
and never needs CORS. Point it elsewhere with `VITE_API_BASE` if you need to.

## Tabs

- **Overview** — headline KPIs, recent inspections, tool status
- **Inspect a Part** — drop in a casting photo and get a live pass/fail plus the
  Hindi operator alert. Try any file from `module1_cv_defect/data/casting/test/`.
- **Quality Inspection** — the full inspection log with stored images
- **Predictive Maintenance** — per-tool RUL charts
- **Demand Forecasting** — per-category history and forecast with P10–P90 bands
- **Benchmarks** / **ROI Calculator**

## What is still static

`src/data/events.json` is no longer the data source, but it is still imported for
the **published model metrics** — benchmark tables, held-out WAPE, Module 1 test
accuracy, cross-validation figures. Those are measured results from the paper
rather than runtime state, so they belong in the repo rather than the database.
Everything else on screen is fetched. See `src/api.js`, which also adapts the
API's camelCase responses into the field names the components read.
