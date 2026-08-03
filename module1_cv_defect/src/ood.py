"""Out-of-distribution detection for the casting classifier.

A softmax classifier has only two answers, so it returns one of them however
unfamiliar the input is -- a photo of something it has never seen scores just as
confidently as a real casting. Confidence alone therefore cannot tell "this is a
good part" from "I have no idea what this is".

This measures distance in feature space instead. The 1280-d penultimate features
of the training set describe what a casting looks like to this model; an image
far from that cloud is something the model was never taught to judge, whatever
its softmax says.

Usage:
    python src/ood.py fit --checkpoint models/casting_mobilenetv2_proper.pt
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

REPO_SRC = Path(__file__).resolve().parent


def extract_features(model, loader, device, limit=None):
    """Penultimate-layer features: everything the classifier sees before deciding."""
    feats = []
    model.eval()
    with torch.no_grad():
        for images, _ in loader:
            images = images.to(device)
            # MobileNetV2: features -> global pool -> classifier. Stop before the head.
            x = model.features(images)
            x = torch.nn.functional.adaptive_avg_pool2d(x, 1).flatten(1)
            feats.append(x.cpu().numpy())
            if limit and sum(len(f) for f in feats) >= limit:
                break
    return np.concatenate(feats)[:limit] if limit else np.concatenate(feats)


def fit(features: np.ndarray, margin: float = 2.2) -> dict:
    """
    Mean and inverse covariance of the training features, plus the distance
    threshold that follows from them. Shrinkage keeps the covariance invertible
    when there are fewer samples than the 1280 dimensions.

    The margin matters. Calibrating the threshold tightly on training data --
    p99.5, say -- rejects most of the held-out test set, because images the model
    merely generalises to sit further out than images it was fitted on. Measured
    on this dataset: training p99.5 is ~25, but held-out test images run to ~46,
    while the nearest genuinely foreign image is ~66. The margin lifts the
    threshold into that gap so honest variation passes and foreign images do not.
    """
    mean = features.mean(axis=0)
    centred = features - mean
    cov = np.cov(centred, rowvar=False)
    cov += np.eye(cov.shape[0]) * (0.1 * np.trace(cov) / cov.shape[0])
    inv_cov = np.linalg.pinv(cov)

    d = mahalanobis(features, mean, inv_cov)
    p99_5 = float(np.percentile(d, 99.5))
    return {
        "mean": mean,
        "inv_cov": inv_cov,
        "threshold": p99_5 * margin,
        "train_median": float(np.median(d)),
        "train_p99_5": p99_5,
        "margin": margin,
    }


def mahalanobis(x: np.ndarray, mean: np.ndarray, inv_cov: np.ndarray) -> np.ndarray:
    """Distance that accounts for how much each feature naturally varies."""
    centred = np.atleast_2d(x) - mean
    return np.sqrt(np.einsum("ij,jk,ik->i", centred, inv_cov, centred))


def main():
    import sys
    sys.path.insert(0, str(REPO_SRC))
    from dataset import get_train_val_test_loaders
    from infer import load_checkpoint

    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["fit"])
    ap.add_argument("--checkpoint", default="models/casting_mobilenetv2_proper.pt")
    ap.add_argument("--data-root", default="data/casting")
    ap.add_argument("--out", default="models/ood_stats.npz")
    ap.add_argument("--margin", type=float, default=2.2,
                    help="lifts the threshold above training-tight calibration; see fit()")
    ap.add_argument("--limit", type=int, default=2000,
                    help="training images to profile; 2000 is plenty for a 1280-d mean")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, image_size = load_checkpoint(args.checkpoint, device)
    # The val loader is the training images under the *clean* transform, which is
    # what inference applies. Profiling the augmented view would widen the cloud
    # with variation that never reaches the model in production.
    _, val_loader, _, _ = get_train_val_test_loaders(
        Path(args.data_root), image_size=image_size, batch_size=32, num_workers=0)

    print(f"profiling up to {args.limit} training images on {device}...")
    feats = extract_features(model, val_loader, device, limit=args.limit)
    print(f"  features: {feats.shape}")

    stats = fit(feats, margin=args.margin)
    np.savez(args.out, mean=stats["mean"], inv_cov=stats["inv_cov"],
             threshold=stats["threshold"])
    print(f"  median train distance : {stats['train_median']:.2f}")
    print(f"  train p99.5           : {stats['train_p99_5']:.2f}")
    print(f"  threshold (x{stats['margin']})       : {stats['threshold']:.2f}")
    print(f"wrote {args.out}")

    meta = Path(args.out).with_suffix(".json")
    meta.write_text(json.dumps({
        "threshold": stats["threshold"],
        "train_median": stats["train_median"],
        "n_images": int(len(feats)),
        "classes": classes,
    }, indent=2))
    print(f"wrote {meta}")


if __name__ == "__main__":
    main()
