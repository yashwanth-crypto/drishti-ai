"""FFT/wavelet feature extraction from raw milling vibration + current signals.

The dataset ships pre-computed time-domain statistics (min/max/mean/std/
skew/kurtosis) per channel, which is what train.py uses for the primary
model. This script does the frequency-domain work the project spec calls
for separately: real FFT-based spectral features and wavelet decomposition
energy, computed directly from the raw per-cutting-pass signal recordings.

Raw files are read by streaming a single entry out of the 24GB zip
archive at a time -- never extracted to disk -- since only a handful of
files are needed to demonstrate the pipeline across a tool's wear
lifecycle, not the full archive.

Usage:
    python src/feature_extraction.py --zip "C:\\ml-data\\drishti-ai\\module3_milling\\archive (1).zip" \\
        --metadata data/FeatureAndMetadata_Milling.csv --tool 9 --sample-every 15 \\
        --out data/tool9_fft_features.csv
"""
import argparse
import zipfile
from io import BytesIO

import numpy as np
import pandas as pd
import pywt

ACCEL_COLS = [
    "Accelerometer - Spindle +Y", "Accelerometer - Spindle -Z", "Accelerometer - Spindle -X",
    "Accelerometer - X Driving axle +Z", "Accelerometer - X Driving axle -X",
    "Accelerometer - Y Driving axle +Z", "Accelerometer - Y Driving axle +Y", "Accelerometer - Y Driving axle -X",
]
CURRENT_COLS = [
    "Current - Spindle L1", "Current - Spindle L2", "Current - Spindle L3",
    "Current - Driving axle X L1", "Current - Driving axle X L2", "Current - Driving axle X L3",
    "Current - Driving axle Y L1", "Current - Driving axle Y L2", "Current - Driving axle Y L3",
    "Current - Driving axle Z L1", "Current - Driving axle Z L2", "Current - Driving axle Z L3",
]


def spectral_features(signal: np.ndarray, fs: float, prefix: str) -> dict:
    signal = signal - np.mean(signal)
    n = len(signal)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    magnitude = np.abs(np.fft.rfft(signal))

    # skip the DC bin (index 0) when finding the dominant frequency
    dominant_idx = np.argmax(magnitude[1:]) + 1 if len(magnitude) > 1 else 0
    energy = float(np.sum(magnitude ** 2))
    centroid = float(np.sum(freqs * magnitude) / np.sum(magnitude)) if np.sum(magnitude) > 0 else 0.0

    return {
        f"{prefix} - dominant_freq": float(freqs[dominant_idx]),
        f"{prefix} - spectral_centroid": centroid,
        f"{prefix} - spectral_energy": energy,
    }


def wavelet_features(signal: np.ndarray, wavelet: str = "db4", level: int = 4, prefix: str = "") -> dict:
    signal = np.array(signal, dtype=np.float64, copy=True)
    signal.setflags(write=True)
    max_level = pywt.dwt_max_level(len(signal), wavelet)
    level = min(level, max_level) if max_level > 0 else 0
    if level == 0:
        return {f"{prefix} - wavelet_energy_L{i}": 0.0 for i in range(level + 1)}

    coeffs = pywt.wavedec(signal, wavelet, level=level)
    return {
        f"{prefix} - wavelet_energy_L{i}": float(np.sum(c ** 2))
        for i, c in enumerate(coeffs)
    }


def extract_features_from_df(df: pd.DataFrame) -> dict:
    features = {}

    acc_dt = np.median(np.diff(df["Timestamps - Acc"].to_numpy()))
    acc_fs = 1.0 / acc_dt if acc_dt > 0 else 1.0
    for col in ACCEL_COLS:
        signal = df[col].to_numpy(dtype=float)
        features.update(spectral_features(signal, acc_fs, col))
        features.update(wavelet_features(signal, prefix=col))

    cur_dt = np.median(np.diff(df["Timestamps - Current"].to_numpy()))
    cur_fs = 1.0 / cur_dt if cur_dt > 0 else 1.0
    for col in CURRENT_COLS:
        signal = df[col].to_numpy(dtype=float)
        features.update(spectral_features(signal, cur_fs, col))
        features.update(wavelet_features(signal, prefix=col))

    return features


def stream_csv_from_zip(zip_path: str, entry_name: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(entry_name) as raw:
            return pd.read_csv(BytesIO(raw.read()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, help="Path to the dataset zip archive")
    parser.add_argument("--metadata", default="data/FeatureAndMetadata_Milling.csv")
    parser.add_argument("--tool", type=int, required=True, help="TollIndex to sample from")
    parser.add_argument("--sample-every", type=int, default=15, help="Take every Nth cycle across the tool's lifecycle")
    parser.add_argument("--out", default="data/fft_features_sample.csv")
    args = parser.parse_args()

    meta = pd.read_csv(args.metadata, sep=";", header=1)
    tool_rows = meta[meta["TollIndex"] == args.tool].sort_values("NumberOfCycle").reset_index(drop=True)
    sampled = tool_rows.iloc[::args.sample_every]

    print(f"Tool {args.tool}: {len(tool_rows)} total cycles, sampling {len(sampled)} across its lifecycle")

    results = []
    for _, row in sampled.iterrows():
        file_name = row["FileName"] + ".csv"
        print(f"  streaming {file_name} ...")
        df = stream_csv_from_zip(args.zip, file_name)
        feats = extract_features_from_df(df)
        feats["FileName"] = row["FileName"]
        feats["CycleToFailure"] = row["CycleToFailure"]
        feats["CycleToFailureNormalized"] = float(str(row["CycleToFailureNormalized"]).replace(",", "."))
        results.append(feats)

    out_df = pd.DataFrame(results)
    out_df.to_csv(args.out, index=False)
    print(f"\nWrote {len(out_df)} rows x {len(out_df.columns)} columns to {args.out}")


if __name__ == "__main__":
    main()
