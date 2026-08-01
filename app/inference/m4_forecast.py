"""Module 4 demand forecaster, served. Same recursive multi-step loop and
signed-log inverse as forecast.py, reusing compute_features so trained and
served features cannot drift.

History can come from the request body, or -- when the caller omits it -- from
the recorded weekly series in data/weekly_category_demand.csv. That file is
gitignored (regenerate it with feature_extraction.py), so the request-body path
is the one that always works."""
import json

import numpy as np
import pandas as pd
import xgboost as xgb

import paths
from features import MIN_HISTORY, compute_features, inverse_signed_log

_point = None
_lower = None
_upper = None
_meta = None


def load():
    global _point, _lower, _upper, _meta
    with open(paths.M4_METADATA) as f:
        _meta = json.load(f)

    def _load_one(path):
        m = xgb.XGBRegressor(enable_categorical=True)
        m.load_model(path)
        return m

    models_dir = paths.M4_MODEL.parent
    _point = _load_one(paths.M4_MODEL)
    _lower = _load_one(models_dir / "demand_forecast_lower.json")
    _upper = _load_one(models_dir / "demand_forecast_upper.json")
    return {
        "categories": len(_meta["categories"]),
        "min_history_weeks": MIN_HISTORY,
        "recorded_history": paths.M4_HISTORY.exists(),
    }


def categories() -> list[str]:
    return list(_meta["categories"])


def recorded_history(category: str) -> list[dict]:
    """The category's real weekly series, as feature_extraction.py wrote it."""
    if not paths.M4_HISTORY.exists():
        raise ValueError(
            f"No recorded history at {paths.M4_HISTORY}. Either pass history in the "
            f"request, or regenerate it with module4_demand_forecasting/src/feature_extraction.py"
        )
    weekly = pd.read_csv(paths.M4_HISTORY, parse_dates=["week"])
    rows = weekly[weekly["Product_Category"] == category].sort_values("week")
    return [
        {"week": str(w.date()), "value": float(v)}
        for w, v in zip(rows["week"], rows["Order_Demand"])
    ]


def forecast(category: str, history: list[dict], horizon: int = 4) -> list[dict]:
    if category not in _meta["categories"]:
        raise ValueError(f"Unknown category '{category}'")
    if len(history) < MIN_HISTORY:
        raise ValueError(
            f"'{category}' has {len(history)} weeks of history, need at least {MIN_HISTORY}"
        )

    ordered = sorted(history, key=lambda r: r["week"])
    values = [float(r["value"]) for r in ordered]
    last_week = pd.Timestamp(ordered[-1]["week"])

    results = []
    for step in range(1, horizon + 1):
        target_week = last_week + pd.Timedelta(weeks=step)
        X = pd.DataFrame([compute_features(np.array(values), target_week)])[_meta["feature_cols"]]

        p = float(inverse_signed_log(_point.predict(X))[0])
        lo = float(inverse_signed_log(_lower.predict(X))[0])
        hi = float(inverse_signed_log(_upper.predict(X))[0])
        lo, hi = min(lo, hi, p), max(lo, hi, p)

        results.append({
            "week": str(target_week.date()),
            "predicted_demand": round(p, 1),
            "lower": round(lo, 1),
            "upper": round(hi, 1),
        })
        values.append(p)

    return results
