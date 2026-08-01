"""Module 1 defect classifier, served. Model loads once at startup instead of
per-call as in infer.py's CLI path; preprocessing and postprocessing are
otherwise identical."""
import io
import time

import torch
import torch.nn.functional as F
from PIL import Image

import paths
from dataset import build_transforms
from infer import load_checkpoint

_model = None
_classes = None
_transform = None
_device = None


def load():
    global _model, _classes, _transform, _device
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model, _classes, image_size = load_checkpoint(str(paths.M1_CHECKPOINT), _device)
    _transform = build_transforms(image_size, train=False)
    return {"device": str(_device), "classes": _classes, "image_size": image_size}


def predict_bytes(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(_device)

    start = time.perf_counter()
    with torch.no_grad():
        probs = F.softmax(_model(tensor), dim=1)[0]
    elapsed_ms = (time.perf_counter() - start) * 1000

    pred_idx = int(probs.argmax().item())
    defect_type = _classes[pred_idx]
    return {
        "pass_fail": "pass" if defect_type == "ok_front" else "fail",
        "defect_type": defect_type,
        "confidence": round(float(probs[pred_idx].item()), 4),
        "inference_ms": round(elapsed_ms, 2),
    }
