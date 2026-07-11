"""Train the Module 4 demand-forecast models.

Three models are trained on the same features:
  - point   : expected next-week demand (squared-error objective)
  - lower   : 10th-percentile forecast (quantile objective, alpha=0.1)
  - upper   : 90th-percentile forecast (quantile objective, alpha=0.9)
The lower/upper pair gives an 80% prediction interval -- for procurement,
"how much might I actually need" is more decision-relevant than a single
point estimate, and the interval width is an honest signal of how much to
trust each category's forecast.

All three train on a signed-log target so categories spanning ~40 to
~25M units/week are weighted comparably (see features.signed_log).

Model-selection notes (from an ablation, see features.py):
  - Fixed 300 trees beat early stopping here -- the natural validation
    window (the tail of the training span) is one late-2015 stretch that
    isn't representative, so early stopping cut training short and raised
    WAPE (~20% -> ~24%).
  - Product_Category as a feature slightly hurt; it's excluded.
  - The extra features (yearly lag, EWMA, trend, cyclical week) net a
    small gain: ~19.9% -> ~19.5% held-out WAPE.

Two evaluations are reported: a single 52-week holdout (the headline,
comparable across changes) and a 3-fold expanding-window time-series CV
(robustness -- one holdout can flatter or punish a model by luck of which
weeks land in it). Split is always BY DATE, never a random shuffle.

Usage:
    python src/train.py --data data/weekly_category_features.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from features import FEATURE_COLS, TARGET, inverse_signed_log, signed_log, wape

TEST_WEEKS = 52

_POINT_PARAMS = dict(
    n_estimators=300, max_depth=5, learning_rate=0.04,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
)
_QUANTILE_PARAMS = dict(
    n_estimators=300, max_depth=5, learning_rate=0.04,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
)


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["week"])
    df["Product_Category"] = df["Product_Category"].astype("category")
    return df


def _fit_point(X, y, seed):
    model = xgb.XGBRegressor(random_state=seed, enable_categorical=True, **_POINT_PARAMS)
    model.fit(X, signed_log(y))
    return model


def _fit_quantile(X, y, alpha, seed):
    model = xgb.XGBRegressor(
        objective="reg:quantileerror", quantile_alpha=alpha,
        random_state=seed, enable_categorical=True, **_QUANTILE_PARAMS,
    )
    model.fit(X, signed_log(y))
    return model


def _metrics(y_true, pred):
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, pred))),
        "mae": float(mean_absolute_error(y_true, pred)),
        "wape_pct": wape(y_true.to_numpy(), pred),
        "r2": float(r2_score(y_true, pred)),
    }


def cross_validate(df, feature_cols, seed, folds=3, test_weeks=26):
    """Expanding-window CV: each fold trains on everything before its test
    window and tests on the next `test_weeks` weeks."""
    last = df["week"].max()
    wapes = []
    for k in range(folds, 0, -1):
        test_start = last - pd.Timedelta(weeks=test_weeks * k) + pd.Timedelta(weeks=1)
        test_end = test_start + pd.Timedelta(weeks=test_weeks)
        tr = df[df["week"] < test_start]
        te = df[(df["week"] >= test_start) & (df["week"] < test_end)]
        if len(te) == 0 or len(tr) == 0:
            continue
        m = _fit_point(tr[feature_cols], tr[TARGET], seed)
        pred = inverse_signed_log(m.predict(te[feature_cols]))
        wapes.append(wape(te[TARGET].to_numpy(), pred))
    return wapes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/weekly_category_features.csv")
    parser.add_argument("--test-weeks", type=int, default=TEST_WEEKS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="models/demand_forecast_xgb.json")
    args = parser.parse_args()

    df = load_data(args.data)
    feature_cols = FEATURE_COLS

    cutoff = df["week"].max() - pd.Timedelta(weeks=args.test_weeks)
    train_df = df[df["week"] < cutoff]
    test_df = df[df["week"] >= cutoff]

    print(f"Cutoff date: {cutoff.date()}")
    print(f"Train rows: {len(train_df)} ({train_df['week'].min().date()} to {train_df['week'].max().date()})")
    print(f"Test rows:  {len(test_df)} ({test_df['week'].min().date()} to {test_df['week'].max().date()})")

    point = _fit_point(train_df[feature_cols], train_df[TARGET], args.seed)
    lower = _fit_quantile(train_df[feature_cols], train_df[TARGET], 0.1, args.seed)
    upper = _fit_quantile(train_df[feature_cols], train_df[TARGET], 0.9, args.seed)

    pred = inverse_signed_log(point.predict(test_df[feature_cols]))
    lo = inverse_signed_log(lower.predict(test_df[feature_cols]))
    hi = inverse_signed_log(upper.predict(test_df[feature_cols]))
    metrics = _metrics(test_df[TARGET], pred)

    # coverage: fraction of actuals inside the [P10, P90] band. a well-
    # calibrated 80% interval should cover ~80%.
    lo_b, hi_b = np.minimum(lo, hi), np.maximum(lo, hi)
    inside = ((test_df[TARGET].to_numpy() >= lo_b) & (test_df[TARGET].to_numpy() <= hi_b)).mean()
    metrics["interval_coverage_pct"] = float(inside * 100)

    cv_wapes = cross_validate(df, feature_cols, args.seed)
    cv_summary = {"folds": [round(w, 1) for w in cv_wapes],
                  "mean_wape_pct": float(np.mean(cv_wapes)) if cv_wapes else None}

    print(f"\nHeld-out (last {args.test_weeks} weeks) forecast metrics:")
    print(f"  RMSE: {metrics['rmse']:,.1f}")
    print(f"  MAE:  {metrics['mae']:,.1f}")
    print(f"  WAPE: {metrics['wape_pct']:.1f}%")
    print(f"  R2:   {metrics['r2']:.4f}")
    print(f"  80% interval coverage: {metrics['interval_coverage_pct']:.1f}% (ideal ~80%)")
    print(f"\n3-fold expanding-window CV WAPE: {cv_summary['folds']}  mean={cv_summary['mean_wape_pct']:.1f}%")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    point.save_model(out_path)
    lower.save_model(out_path.parent / "demand_forecast_lower.json")
    upper.save_model(out_path.parent / "demand_forecast_upper.json")

    metadata = {
        "feature_cols": feature_cols,
        "target": TARGET,
        "categories": sorted(df["Product_Category"].cat.categories.tolist()),
        "cutoff_date": str(cutoff.date()),
        "test_weeks": args.test_weeks,
        "metrics": metrics,
        "cv": cv_summary,
    }
    with open(out_path.parent / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved point/lower/upper models to {out_path.parent}/")


if __name__ == "__main__":
    main()
