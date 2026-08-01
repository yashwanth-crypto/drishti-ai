"""Module 3 tool-wear RUL regressor, served. Mirrors the inline prediction in
streaming_replay.py (clip to [0,1], alert below WEAR_ALERT_THRESHOLD) but takes
a feature dict per request instead of replaying rows off a CSV."""
import json

import numpy as np
import pandas as pd
import xgboost as xgb

import paths
from streaming_replay import WEAR_ALERT_THRESHOLD

_model = None
_feature_cols = None


def load():
    global _model, _feature_cols
    with open(paths.M3_METADATA) as f:
        meta = json.load(f)
    _feature_cols = meta["feature_cols"]
    _model = xgb.XGBRegressor()
    _model.load_model(paths.M3_MODEL)
    return {"n_features": len(_feature_cols), "wear_alert_threshold": WEAR_ALERT_THRESHOLD}


def feature_cols() -> list[str]:
    return list(_feature_cols)


def predict(features: dict) -> dict:
    missing = [c for c in _feature_cols if c not in features]
    if missing:
        raise ValueError(f"Missing {len(missing)} feature(s), e.g. {missing[:5]}")

    X = pd.DataFrame([features])[_feature_cols]
    predicted_rul = float(np.clip(_model.predict(X)[0], 0.0, 1.0))
    return {
        "predicted_rul": round(predicted_rul, 4),
        "wear_alert": predicted_rul < WEAR_ALERT_THRESHOLD,
    }
