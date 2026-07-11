"""Train an XGBoost regressor to predict remaining tool life (RUL) from
per-cutting-pass statistical features (vibration + current sensors).

Dataset: Piecuch & Zabinski 2025 CNC milling dataset (968 cutting passes,
14 physical tools tracked from fresh to failure). The dataset ships
pre-computed time-domain statistical features (min/max/mean/std/skew/
kurtosis) per sensor channel per cutting pass, plus the ground-truth
label CycleToFailureNormalized (1.0 = fresh tool, 0.0 = failure).

Train/test split is BY TOOL, not by row: rows from the same physical tool
are highly correlated (consecutive cycles of its own wear curve), so a
random row split would let the model "cheat" by interpolating within a
tool it already partly saw. Splitting by tool tests what actually matters:
generalizing to a tool the model has never seen.

Usage:
    python src/train.py --data data/FeatureAndMetadata_Milling.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

TARGET = "CycleToFailureNormalized"
NON_FEATURE_COLS = [
    "FileName", "NumberOfCycle", "SampleIndex", "TollIndex",
    "CycleToFailure", "CycleToFailureNormalized",
]


def load_data(path: str) -> pd.DataFrame:
    # Most numeric columns use '.' as the decimal separator, but
    # HardnessMean and RDOC are exported with ',' for some rows (a quirk
    # of the source file) -- fix those columns by hand rather than
    # mis-parsing everything else.
    df = pd.read_csv(path, sep=";", header=1)
    for col in ["HardnessMean", "RDOC", "CycleToFailureNormalized"]:
        df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
    # TollIndex 11 has a single recorded cycle -- not usable for a
    # meaningful train or test fold, so it's dropped rather than silently
    # misrepresented as an evaluated tool.
    df = df[df["TollIndex"] != 11].reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/FeatureAndMetadata_Milling.csv")
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="models/tool_wear_xgb.json")
    args = parser.parse_args()

    df = load_data(args.data)
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]

    X = df[feature_cols]
    y = df[TARGET]
    groups = df["TollIndex"]

    splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
    train_idx, test_idx = next(splitter.split(X, y, groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    test_tools = sorted(groups.iloc[test_idx].unique().tolist())
    train_tools = sorted(groups.iloc[train_idx].unique().tolist())

    print(f"Train tools ({len(train_tools)}): {train_tools}")
    print(f"Test tools (held out, {len(test_tools)}): {test_tools}")
    print(f"Train rows: {len(X_train)}, test rows: {len(X_test)}")

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=args.seed,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    pred = np.clip(pred, 0.0, 1.0)

    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mae = float(mean_absolute_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))

    print(f"\nHeld-out (unseen tools) RUL-fraction metrics:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE:  {mae:.4f}")
    print(f"  R2:   {r2:.4f}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(out_path)

    metadata = {
        "feature_cols": feature_cols,
        "target": TARGET,
        "train_tools": train_tools,
        "test_tools": test_tools,
        "metrics": {"rmse": rmse, "mae": mae, "r2": r2},
    }
    with open(out_path.parent / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model to {out_path}")


if __name__ == "__main__":
    main()
