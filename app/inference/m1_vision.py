"""Module 1 defect classifier, served. Model loads once at startup instead of
per-call as in infer.py's CLI path; preprocessing and postprocessing are
otherwise identical."""
import io
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

import paths
from dataset import build_transforms
from infer import load_checkpoint
from ood import mahalanobis

_model = None
_classes = None
_transform = None
_device = None
_ood = None


def load():
    global _model, _classes, _transform, _device, _ood
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model, _classes, image_size = load_checkpoint(str(paths.M1_CHECKPOINT), _device)
    _transform = build_transforms(image_size, train=False)

    # Optional: without it the service still runs, it just cannot tell an
    # unfamiliar image from a familiar one.
    if paths.M1_OOD_STATS.exists():
        s = np.load(paths.M1_OOD_STATS)
        _ood = {"mean": s["mean"], "inv_cov": s["inv_cov"], "threshold": float(s["threshold"])}

    return {
        "device": str(_device),
        "classes": _classes,
        "image_size": image_size,
        "ood_threshold": _ood["threshold"] if _ood else None,
    }


def predict_bytes(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(_device)

    start = time.perf_counter()
    with torch.no_grad():
        features = torch.nn.functional.adaptive_avg_pool2d(
            _model.features(tensor), 1).flatten(1)
        probs = F.softmax(_model.classifier(features), dim=1)[0]
    elapsed_ms = (time.perf_counter() - start) * 1000

    pred_idx = int(probs.argmax().item())
    defect_type = _classes[pred_idx]

    # How far this image sits from the parts the model was trained on. Softmax
    # cannot answer that -- random noise scores 0.999 confident.
    recognised, distance = True, None
    if _ood:
        distance = float(mahalanobis(features.cpu().numpy(), _ood["mean"], _ood["inv_cov"])[0])
        recognised = distance <= _ood["threshold"]

    return {
        "pass_fail": "pass" if defect_type == "ok_front" else "fail",
        "defect_type": defect_type,
        "confidence": round(float(probs[pred_idx].item()), 4),
        "inference_ms": round(elapsed_ms, 2),
        "recognised": recognised,
        "ood_distance": round(distance, 2) if distance is not None else None,
    }
