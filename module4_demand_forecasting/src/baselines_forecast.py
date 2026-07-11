"""Baseline forecasters for Module 4, so the XGBoost WAPE has something to
beat. A 19.7% WAPE is only meaningful relative to trivial predictors.

Baselines, all evaluated on the SAME held-out test rows as the model:
  - Naive (last value):     next week = last week's actual   (= lag_1)
  - Seasonal-naive (yearly): next week = value 52 weeks ago  (= lag_52)
  - Prophet (optional):     per-category additive model with yearly
                            seasonality, if the `prophet` package installs.

The naive predictors come straight from the lag columns already in the
feature table, so they are computed on exactly the model's test rows for
a fair, aligned comparison.

Usage:
    python src/baselines_forecast.py
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from features import TARGET, wape
from train import load_data


def naive_baselines(features_csv, model_dir):
    with open(Path(model_dir) / "model_metadata.json") as f:
        meta = json.load(f)
    df = load_data(features_csv)
    test = df[df["week"] >= pd.Timestamp(meta["cutoff_date"])]
    y = test[TARGET].to_numpy()
    results = {
        "model_xgboost": meta["metrics"]["wape_pct"],
        "naive_last_value": wape(y, test["lag_1"].to_numpy()),
        "seasonal_naive_52w": wape(y, test["lag_52"].to_numpy()),
    }
    return results, meta


def prophet_baseline(history_csv, meta):
    try:
        from prophet import Prophet
    except Exception as e:
        print(f"  (Prophet not available: {e})")
        return None

    import logging
    logging.getLogger("prophet").setLevel(logging.ERROR)
    logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

    weekly = pd.read_csv(history_csv, parse_dates=["week"])
    cutoff = pd.Timestamp(meta["cutoff_date"])
    all_true, all_pred = [], []

    for cat in meta["categories"]:
        s = weekly[weekly["Product_Category"] == cat].sort_values("week")
        train = s[s["week"] < cutoff]
        test = s[s["week"] >= cutoff]
        if len(train) < 60 or len(test) == 0:
            continue
        dfp = train.rename(columns={"week": "ds", "Order_Demand": "y"})[["ds", "y"]]
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(dfp)
        future = test[["week"]].rename(columns={"week": "ds"})
        fc = m.predict(future)
        all_true.extend(test["Order_Demand"].tolist())
        all_pred.extend(fc["yhat"].tolist())

    return wape(pd.Series(all_true).to_numpy(), pd.Series(all_pred).to_numpy())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/weekly_category_features.csv")
    ap.add_argument("--history", default="data/weekly_category_demand.csv")
    ap.add_argument("--model-dir", default="models")
    ap.add_argument("--skip-prophet", action="store_true")
    args = ap.parse_args()

    results, meta = naive_baselines(args.features, args.model_dir)

    print("Held-out WAPE comparison (lower is better):")
    print(f"  Seasonal-naive (52w) : {results['seasonal_naive_52w']:.1f}%")
    print(f"  Naive (last value)   : {results['naive_last_value']:.1f}%")

    if not args.skip_prophet:
        print("  Fitting Prophet per category (this can take a minute)...")
        p = prophet_baseline(args.history, meta)
        if p is not None:
            results["prophet"] = p
            print(f"  Prophet              : {p:.1f}%")

    print(f"  XGBoost (ours)       : {results['model_xgboost']:.1f}%")

    out = Path(args.model_dir) / "baseline_comparison.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
