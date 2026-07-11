"""Baselines for Module 3 (tool-wear RUL), so the XGBoost R2 has context.

Same by-tool split as the model (test tools from model_metadata.json).
Baselines:
  - Constant mean: predict the mean training RUL fraction for every row
    (R2 ~ 0 by construction -- the "no skill" reference).
  - Linear regression on the same features (a simple parametric model).
Both compared against the trained XGBoost.

Usage:
    python src/baselines_pdm.py
"""
import json
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from train import NON_FEATURE_COLS, TARGET, load_data


def metrics(y, p):
    p = np.clip(p, 0.0, 1.0)
    return (float(np.sqrt(mean_squared_error(y, p))),
            float(mean_absolute_error(y, p)),
            float(r2_score(y, p)))


def main():
    with open("models/model_metadata.json") as f:
        meta = json.load(f)
    test_tools = meta["test_tools"]

    df = load_data("data/FeatureAndMetadata_Milling.csv")
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]

    test = df[df["TollIndex"].isin(test_tools)]
    train = df[~df["TollIndex"].isin(test_tools)]
    ytr, yte = train[TARGET].to_numpy(), test[TARGET].to_numpy()

    imp = SimpleImputer(strategy="median")
    Xtr = imp.fit_transform(train[feature_cols])
    Xte = imp.transform(test[feature_cols])

    print("Held-out (unseen tools) RUL metrics  [RMSE / MAE / R2]:")

    const = np.full_like(yte, ytr.mean())
    print("  Constant mean      : %.3f / %.3f / %.3f" % metrics(yte, const))

    lin = LinearRegression().fit(Xtr, ytr)
    print("  Linear regression  : %.3f / %.3f / %.3f" % metrics(yte, lin.predict(Xte)))

    xm = meta["metrics"]
    print("  XGBoost (ours)     : %.3f / %.3f / %.3f" % (xm["rmse"], xm["mae"], xm["r2"]))

    out = Path("models/baseline_comparison_pdm.json")
    with open(out, "w") as f:
        json.dump({
            "constant_mean": dict(zip(["rmse", "mae", "r2"], metrics(yte, const))),
            "linear_regression": dict(zip(["rmse", "mae", "r2"], metrics(yte, lin.predict(Xte)))),
            "xgboost": {"rmse": xm["rmse"], "mae": xm["mae"], "r2": xm["r2"]},
        }, f, indent=2)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
