"""Evaluate the trained point model on its held-out (future) weeks, with a
per-category breakdown.

Usage:
    python src/evaluate.py --model models/demand_forecast_xgb.json --data data/weekly_category_features.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from features import TARGET, inverse_signed_log, wape
from train import load_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/demand_forecast_xgb.json")
    parser.add_argument("--data", default="data/weekly_category_features.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    with open(model_path.parent / "model_metadata.json") as f:
        meta = json.load(f)

    df = load_data(args.data)
    cutoff = pd.Timestamp(meta["cutoff_date"])
    test_df = df[df["week"] >= cutoff]

    model = xgb.XGBRegressor(enable_categorical=True)
    model.load_model(model_path)

    X_test = test_df[meta["feature_cols"]]
    y_test = test_df[TARGET]
    pred = inverse_signed_log(model.predict(X_test))

    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mae = float(mean_absolute_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))
    wape_pct = wape(y_test.to_numpy(), pred)

    print(f"Held-out period: {cutoff.date()} onward ({len(test_df)} category-weeks)")
    print(f"Overall: RMSE={rmse:,.1f}  MAE={mae:,.1f}  WAPE={wape_pct:.1f}%  R2={r2:.4f}\n")

    print("Per-category breakdown (sorted by WAPE, worst first):")
    rows = []
    for cat in meta["categories"]:
        mask = (test_df["Product_Category"] == cat).to_numpy()
        if mask.sum() == 0:
            continue
        cat_wape = wape(y_test[mask].to_numpy(), pred[mask])
        cat_mae = float(mean_absolute_error(y_test[mask], pred[mask]))
        rows.append((cat, int(mask.sum()), float(y_test[mask].mean()), cat_mae, cat_wape))

    rows.sort(key=lambda r: r[4], reverse=True)
    for cat, n, mean_actual, cat_mae, cat_wape in rows:
        print(f"  {cat}: n={n:3d}  mean_actual={mean_actual:>14,.0f}  MAE={cat_mae:>12,.0f}  WAPE={cat_wape:6.1f}%")


if __name__ == "__main__":
    main()
