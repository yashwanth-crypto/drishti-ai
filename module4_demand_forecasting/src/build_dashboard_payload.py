"""Build the Module 4 slice of the dashboard's events.json.

Picks a small, honest spread of categories to display rather than all
28 -- best WAPE, worst WAPE, and a few representative mid-range/large-
scale ones -- so the dashboard doesn't quietly hide the categories the
model is bad at behind the ones it's good at.

Usage:
    python src/build_dashboard_payload.py --out ../dashboard/src/data/module4_forecast.json
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import xgboost as xgb

from features import TARGET, inverse_signed_log, wape
from forecast import forecast_category
from train import load_data

DASHBOARD_CATEGORIES = [
    "Category_019",  # best WAPE, huge scale
    "Category_005",  # good WAPE, large scale
    "Category_006",  # mid WAPE, large scale
    "Category_001",  # good WAPE, mid scale
    "Category_031",  # mid WAPE, tiny scale
    "Category_020",  # worst WAPE, mid scale
]
HISTORY_WEEKS_SHOWN = 16
FORECAST_HORIZON = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/weekly_category_features.csv")
    parser.add_argument("--history", default="data/weekly_category_demand.csv")
    parser.add_argument("--model", default="models/demand_forecast_xgb.json")
    parser.add_argument("--out", default="../dashboard/src/data/module4_forecast.json")
    args = parser.parse_args()

    model_path = Path(args.model)
    with open(model_path.parent / "model_metadata.json") as f:
        meta = json.load(f)

    df = load_data(args.features)
    cutoff = pd.Timestamp(meta["cutoff_date"])
    test_df = df[df["week"] >= cutoff]

    model = xgb.XGBRegressor(enable_categorical=True)
    model.load_model(model_path)
    pred = inverse_signed_log(model.predict(test_df[meta["feature_cols"]]))

    weekly = pd.read_csv(args.history, parse_dates=["week"])

    categories_out = []
    for cat in DASHBOARD_CATEGORIES:
        mask = (test_df["Product_Category"] == cat).to_numpy()
        cat_wape = wape(test_df[TARGET][mask].to_numpy(), pred[mask])
        mean_weekly = float(test_df[TARGET][mask].mean())

        recent = weekly[weekly["Product_Category"] == cat].sort_values("week").tail(HISTORY_WEEKS_SHOWN)
        history = [
            {"week": str(row.week.date()), "actual_demand": float(row.Order_Demand)}
            for row in recent.itertuples()
        ]
        forecast = forecast_category(cat, FORECAST_HORIZON, args.history, args.model)

        categories_out.append({
            "category": cat,
            "wape_pct": round(cat_wape, 1),
            "mean_weekly_demand": round(mean_weekly, 1),
            "history": history,
            "forecast": forecast,
        })

    payload = {
        "model_metrics": meta["metrics"],
        "cv": meta.get("cv"),
        "cutoff_date": meta["cutoff_date"],
        "test_weeks": meta["test_weeks"],
        "categories_modeled": len(meta["categories"]),
        "categories": categories_out,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote Module 4 dashboard payload ({len(categories_out)} categories) to {out_path}")


if __name__ == "__main__":
    main()
