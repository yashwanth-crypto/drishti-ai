"""Simulated real-time replay of tool-wear sensor readings through the trained model.

This is a REPLAY of a static, already-recorded dataset, row by row, with a
delay between rows to imitate a live sensor feed -- there is no real
sensor hardware involved. Any "live"/"real-time" framing of this script's
output must say so explicitly (see project spec honesty boundaries).

Usage:
    python src/streaming_replay.py --tool 9 --interval 0.5
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xgboost as xgb

from train import TARGET, load_data

WEAR_ALERT_THRESHOLD = 0.2  # RUL fraction below this triggers a maintenance alert


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/tool_wear_xgb.json")
    parser.add_argument("--data", default="data/FeatureAndMetadata_Milling.csv")
    parser.add_argument("--tool", type=int, required=True, help="TollIndex to replay")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between simulated readings")
    args = parser.parse_args()

    model_path = Path(args.model)
    with open(model_path.parent / "model_metadata.json") as f:
        meta = json.load(f)

    model = xgb.XGBRegressor()
    model.load_model(model_path)

    df = load_data(args.data)
    tool_df = df[df["TollIndex"] == args.tool].sort_values("NumberOfCycle").reset_index(drop=True)
    if tool_df.empty:
        print(f"No cycles found for tool {args.tool}")
        return

    print(f"[SIMULATED REPLAY] Tool {args.tool}, {len(tool_df)} cycles, "
          f"{args.interval}s between readings -- not live sensor data.\n")

    for idx, row in tool_df.iterrows():
        X = tool_df.loc[[idx], meta["feature_cols"]]
        predicted_rul = float(np.clip(model.predict(X)[0], 0.0, 1.0))
        actual_rul = float(row[TARGET])

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": "3",
            "event_type": "maintenance_alert" if predicted_rul < WEAR_ALERT_THRESHOLD else "sensor_reading",
            "payload": {
                "simulated": True,
                "tool_id": int(args.tool),
                "cycle": int(row["NumberOfCycle"]),
                "predicted_rul_fraction": round(predicted_rul, 4),
                "actual_rul_fraction": round(actual_rul, 4),
                "wear_alert": predicted_rul < WEAR_ALERT_THRESHOLD,
            },
        }
        print(json.dumps(event))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
