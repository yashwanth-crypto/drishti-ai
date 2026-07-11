"""Report Module 4 held-out metrics across several seeds (mean +/- std),
to show the forecast result is stable and not a single-seed artefact.

Trains only the point model per seed in memory and evaluates on the same
held-out 52 weeks; it does NOT overwrite the canonical saved models.

Usage:
    python src/multiseed_m4.py --seeds 42 1 2
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from features import FEATURE_COLS, TARGET, inverse_signed_log, wape
from train import _fit_point, cross_validate, load_data, TEST_WEEKS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/weekly_category_features.csv")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1, 2])
    args = ap.parse_args()

    df = load_data(args.data)
    cutoff = df["week"].max() - pd.Timedelta(weeks=TEST_WEEKS)
    train_df, test_df = df[df["week"] < cutoff], df[df["week"] >= cutoff]
    y = test_df[TARGET]

    wapes, r2s, cvs = [], [], []
    for seed in args.seeds:
        m = _fit_point(train_df[FEATURE_COLS], train_df[TARGET], seed)
        pred = inverse_signed_log(m.predict(test_df[FEATURE_COLS]))
        w = wape(y.to_numpy(), pred)
        r2 = float(r2_score(y, pred))
        cv = float(np.mean(cross_validate(df, FEATURE_COLS, seed)))
        wapes.append(w); r2s.append(r2); cvs.append(cv)
        print(f"  seed {seed:>2}: WAPE={w:.2f}%  R2={r2:.4f}  CV_WAPE={cv:.2f}%")

    def ms(a):
        a = np.array(a)
        return f"{a.mean():.2f} +/- {a.std(ddof=0):.2f}"

    print(f"\nAcross {len(args.seeds)} seeds:")
    print(f"  Held-out WAPE : {ms(wapes)} %")
    print(f"  R2            : {ms(r2s)}")
    print(f"  CV mean WAPE  : {ms(cvs)} %")


if __name__ == "__main__":
    main()
