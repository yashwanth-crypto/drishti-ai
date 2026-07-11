"""Forecast-query function: given a product category, predict its demand
for the next N weeks, with an 80% prediction interval.

The models are one-step-ahead predictors. Multi-week horizons use
recursive forecasting: predict week 1, append the point (median) forecast
to the category's history, recompute features from the extended history,
predict week 2, and so on. Standard for tree-based one-step models, but
errors compound with horizon -- treat later weeks as less reliable than
week 1, which is also why the returned interval matters.

Known data-boundary caveat: the raw dataset's final recorded week shows a
sharp demand drop-off across nearly every category (e.g. Category_019
falls from a ~17M/week run rate to a few thousand). That reads as
truncated end-of-collection data, not a real collapse, and the first
forecast point -- seeded from those final weeks -- inherits the
distortion. Documented rather than patched, since silently editing real
recorded values would be its own honesty problem.

Usage:
    python src/forecast.py --category Category_019 --horizon 4
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from features import MIN_HISTORY, compute_features, inverse_signed_log


def _load_models(model_path: Path):
    def load(p):
        m = xgb.XGBRegressor(enable_categorical=True)
        m.load_model(p)
        return m
    return (
        load(model_path),
        load(model_path.parent / "demand_forecast_lower.json"),
        load(model_path.parent / "demand_forecast_upper.json"),
    )


def forecast_category(
    category: str,
    horizon: int = 4,
    history_path: str = "data/weekly_category_demand.csv",
    model_path: str = "models/demand_forecast_xgb.json",
) -> list[dict]:
    model_path = Path(model_path)
    with open(model_path.parent / "model_metadata.json") as f:
        meta = json.load(f)

    if category not in meta["categories"]:
        raise ValueError(f"Unknown category '{category}'. Known: {meta['categories']}")

    weekly = pd.read_csv(history_path, parse_dates=["week"])
    cat_history = weekly[weekly["Product_Category"] == category].sort_values("week")
    if len(cat_history) < MIN_HISTORY:
        raise ValueError(
            f"'{category}' only has {len(cat_history)} weeks of history, "
            f"need at least {MIN_HISTORY} to forecast."
        )

    point, lower, upper = _load_models(model_path)

    history = cat_history["Order_Demand"].to_numpy(dtype=float).tolist()
    last_week = cat_history["week"].max()

    results = []
    for step in range(1, horizon + 1):
        target_week = last_week + pd.Timedelta(weeks=step)
        feat = compute_features(np.array(history), target_week)
        X = pd.DataFrame([feat])[meta["feature_cols"]]

        p = float(inverse_signed_log(point.predict(X))[0])
        lo = float(inverse_signed_log(lower.predict(X))[0])
        hi = float(inverse_signed_log(upper.predict(X))[0])
        # quantile models can cross; keep the band consistent around the point
        lo, hi = min(lo, hi, p), max(lo, hi, p)

        results.append({
            "week": str(target_week.date()),
            "predicted_demand": round(p, 1),
            "lower": round(lo, 1),
            "upper": round(hi, 1),
        })
        history.append(p)  # recurse on the point forecast

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True)
    parser.add_argument("--horizon", type=int, default=4)
    parser.add_argument("--history", default="data/weekly_category_demand.csv")
    parser.add_argument("--model", default="models/demand_forecast_xgb.json")
    args = parser.parse_args()

    forecast = forecast_category(args.category, args.horizon, args.history, args.model)
    print(f"Forecast for {args.category} (next {args.horizon} weeks):")
    for row in forecast:
        print(f"  {row['week']}: {row['predicted_demand']:>14,.1f}  [P10 {row['lower']:>14,.1f}  P90 {row['upper']:>14,.1f}]")


if __name__ == "__main__":
    main()
