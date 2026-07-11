"""Clean the raw Kaggle order-demand log and turn it into a weekly,
per-category feature table an XGBoost regressor can train on.

Raw data is per-order, per-product (2,160 distinct products, ~1.05M rows,
2011-01 to 2017-01). Forecasting at the individual-product level would be
too sparse for most products to learn anything from -- instead this
aggregates to weekly demand per Product_Category (33 categories), which
is also the more useful granularity for MSME raw-material/consumable
procurement planning than single-SKU forecasts.

Feature engineering itself lives in features.py so training and recursive
forecasting share one implementation. This script's job is the cleaning,
weekly aggregation, and applying that shared builder row-by-row.

Known raw-data quirks handled here:
- ~1.1% of rows have an unparseable/missing Date -- dropped.
- Order_Demand is a string column; returns/cancellations are encoded as
  "(123)" instead of "-123" -- parsed into a signed int.
- A handful of categories only have a few weeks of history (e.g.
  Category_027 has 19 weeks) -- too little to hold out a test period
  from, so they're dropped rather than trained on and scored on near-
  zero data.

Usage:
    python src/feature_extraction.py --data "data/Historical Product Demand.csv" \\
        --out data/weekly_category_features.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from features import MIN_HISTORY, TARGET, VALUE_FEATURES, compute_features

MIN_WEEKS_PER_CATEGORY = 100


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).copy()

    is_return = df["Order_Demand"].str.contains(r"\(", regex=True)
    magnitude = df["Order_Demand"].str.replace(r"[()]", "", regex=True).astype(int)
    df["Order_Demand"] = np.where(is_return, -magnitude, magnitude)

    df["week"] = df["Date"].dt.to_period("W").dt.start_time
    return df


def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = (
        df.groupby(["Product_Category", "week"])["Order_Demand"]
        .sum()
        .reset_index()
        .sort_values(["Product_Category", "week"])
    )

    week_counts = weekly.groupby("Product_Category").size()
    keep = week_counts[week_counts >= MIN_WEEKS_PER_CATEGORY].index
    dropped = sorted(set(week_counts.index) - set(keep))
    if dropped:
        print(f"Dropping {len(dropped)} categories with < {MIN_WEEKS_PER_CATEGORY} weeks of history: {dropped}")
    return weekly[weekly["Product_Category"].isin(keep)].reset_index(drop=True)


def build_features(weekly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, grp in weekly.groupby("Product_Category", observed=True):
        grp = grp.sort_values("week")
        values = grp["Order_Demand"].to_numpy(dtype=float)
        weeks = grp["week"].tolist()
        # start once MIN_HISTORY prior weeks exist, so every feature is defined
        for i in range(MIN_HISTORY, len(grp)):
            feat = compute_features(values[:i], weeks[i])
            feat["Product_Category"] = category
            feat["week"] = weeks[i]
            feat[TARGET] = float(values[i])
            rows.append(feat)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/Historical Product Demand.csv")
    parser.add_argument("--out", default="data/weekly_category_features.csv")
    args = parser.parse_args()

    df = load_and_clean(args.data)
    print(f"Loaded {len(df)} cleaned order rows, {df['Product_Category'].nunique()} categories")

    weekly = aggregate_weekly(df)
    features = build_features(weekly)

    # Raw weekly series, kept so forecast.py can seed recursive forecasts
    # from real recent history without rebuilding lag columns.
    raw_out = Path(args.out).with_name("weekly_category_demand.csv")
    weekly.to_csv(raw_out, index=False)

    ordered = ["Product_Category", "week", TARGET] + VALUE_FEATURES
    features[ordered].to_csv(args.out, index=False)
    print(f"Wrote {len(features)} rows x {len(ordered)} columns to {args.out}")
    print(f"Categories retained: {features['Product_Category'].nunique()}")
    print(f"Week range: {features['week'].min().date()} to {features['week'].max().date()}")


if __name__ == "__main__":
    main()
