"""Single source of truth for Module 4's feature engineering.

Both the batch feature builder (feature_extraction.py) and the recursive
multi-step forecaster (forecast.py) call compute_features() here, so the
features a row is TRAINED on and the features it's later PREDICTED from
can never silently drift apart -- a class of bug that's easy to introduce
when training and inference build their feature vectors in two places.

Lags are positional (N recorded weeks back), matching how the weekly
series is aggregated. Most categories are dense (~one row per calendar
week), so lag_52 approximates "same week last year"; a category with
gaps would have a slightly off yearly alignment -- acceptable for this
prototype, noted rather than papered over.
"""
import numpy as np
import pandas as pd

# Positional lags, in weeks. lag_52 captures yearly seasonality.
LAGS = [1, 2, 3, 4, 8, 12, 52]

# Weeks of prior history a row needs before every feature is defined.
MIN_HISTORY = max(LAGS)

# Canonical feature set the models actually train on. These are the
# value-series-derived features only.
#
# Product_Category is deliberately NOT a model feature: an ablation
# (src history / commit notes) showed adding it as a categorical feature
# slightly WORSENED held-out WAPE (19.5% -> 20.0%). The lag/rolling
# features already encode each category's demand level, so the category
# id adds mostly overfitting room, not signal.
VALUE_FEATURES = [
    *[f"lag_{lag}" for lag in LAGS],
    "rolling_mean_4", "rolling_std_4", "rolling_mean_8", "rolling_mean_13",
    "ewma_4", "trend_1", "trend_4",
    "month", "weekofyear", "woy_sin", "woy_cos",
]
FEATURE_COLS = list(VALUE_FEATURES)

TARGET = "Order_Demand"


def signed_log(y):
    """Sign-preserving log1p, so a 10x demand swing at 40 units/week
    weighs like a 10x swing at 15M units/week. See train.py for the
    before/after numbers that justified this."""
    y = np.asarray(y, dtype=float)
    return np.sign(y) * np.log1p(np.abs(y))


def inverse_signed_log(y):
    y = np.asarray(y, dtype=float)
    return np.sign(y) * np.expm1(np.abs(y))


def wape(y_true, y_pred) -> float:
    """Weighted absolute percentage error: sum(|error|)/sum(|actual|).

    Standard for demand forecasting across series of very different
    scale. Plain row-wise MAPE blows up to thousands of percent here
    purely from low-volume weeks (actual demand in the tens), so it's
    not reported. WAPE weights every unit of demand equally.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.sum(np.abs(y_true))
    return float(np.sum(np.abs(y_true - y_pred)) / denom * 100) if denom else float("nan")


def compute_features(history: np.ndarray, target_week: pd.Timestamp) -> dict:
    """Build one feature row from the demand values strictly BEFORE
    target_week (chronological, most-recent last). Requires
    len(history) >= MIN_HISTORY."""
    h = np.asarray(history, dtype=float)
    feat = {f"lag_{lag}": float(h[-lag]) for lag in LAGS}

    feat["rolling_mean_4"] = float(h[-4:].mean())
    feat["rolling_std_4"] = float(h[-4:].std(ddof=1))
    feat["rolling_mean_8"] = float(h[-8:].mean())
    feat["rolling_mean_13"] = float(h[-13:].mean())
    feat["ewma_4"] = float(pd.Series(h[-13:]).ewm(span=4).mean().iloc[-1])
    feat["trend_1"] = float(h[-1] - h[-2])
    feat["trend_4"] = float(h[-1] - h[-4])

    woy = int(target_week.isocalendar()[1])
    feat["month"] = int(target_week.month)
    feat["weekofyear"] = woy
    feat["woy_sin"] = float(np.sin(2 * np.pi * woy / 52))
    feat["woy_cos"] = float(np.cos(2 * np.pi * woy / 52))
    return feat
