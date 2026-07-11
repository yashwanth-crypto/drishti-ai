"""Evaluate a trained tool-wear model on its held-out (unseen) test tools.

Usage:
    python src/evaluate.py --model models/tool_wear_xgb.json --data data/FeatureAndMetadata_Milling.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from train import TARGET, load_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/tool_wear_xgb.json")
    parser.add_argument("--data", default="data/FeatureAndMetadata_Milling.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    with open(model_path.parent / "model_metadata.json") as f:
        meta = json.load(f)

    df = load_data(args.data)
    test_df = df[df["TollIndex"].isin(meta["test_tools"])]

    model = xgb.XGBRegressor()
    model.load_model(model_path)

    X_test = test_df[meta["feature_cols"]]
    y_test = test_df[TARGET]
    pred = np.clip(model.predict(X_test), 0.0, 1.0)

    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mae = float(mean_absolute_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))

    print(f"Held-out tools: {meta['test_tools']}")
    print(f"Overall: RMSE={rmse:.4f}  MAE={mae:.4f}  R2={r2:.4f}\n")

    print("Per-tool breakdown:")
    for tool in meta["test_tools"]:
        mask = test_df["TollIndex"] == tool
        tool_rmse = float(np.sqrt(mean_squared_error(y_test[mask], pred[mask])))
        tool_mae = float(mean_absolute_error(y_test[mask], pred[mask]))
        print(f"  Tool {tool}: n={mask.sum():3d}  RMSE={tool_rmse:.4f}  MAE={tool_mae:.4f}")


if __name__ == "__main__":
    main()
