# -*- coding: utf-8 -*-
"""Regenerate the dashboard's inspection log (and its KPIs) from the
CORRECTED Module 1 model, pairing each real prediction with its Module 2
Hindi alert. Replaces the stale inspection entries that came from the
original (test-selected) checkpoint. Maintenance and forecasting sections
are preserved; only inspections + the inspection-related KPIs are rebuilt.

Run inference on CPU so it doesn't contend with any GPU training.

Usage:
    python build_events.py
"""
import base64
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "module1_cv_defect" / "src"))
sys.path.insert(0, str(ROOT / "module2_vernacular_alert" / "src"))

from dataset import build_transforms          # noqa: E402
from model import build_model                 # noqa: E402
from alerts import generate_alert             # noqa: E402

CKPT = ROOT / "module1_cv_defect" / "models" / "casting_mobilenetv2_proper.pt"
TEST = ROOT / "module1_cv_defect" / "data" / "casting" / "test"
EVENTS = ROOT / "dashboard" / "src" / "data" / "events.json"
M1_MEAN_TEST_ACC = 0.9939   # 3-seed mean (reported headline)
M4_WAPE = 19.6              # 3-seed mean held-out WAPE

# a realistic mix; evenly sampled from each class folder
N_DEF, N_OK = 10, 14


def sample(folder, n):
    files = sorted(folder.glob("*.jpeg"))
    step = max(len(files) // n, 1)
    return files[::step][:n]


def thumb_b64(img):
    t = img.copy()
    t.thumbnail((128, 128))
    buf = BytesIO()
    t.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def main():
    device = torch.device("cpu")
    ckpt = torch.load(CKPT, map_location=device)
    classes, image_size = ckpt["classes"], ckpt["image_size"]
    model = build_model(num_classes=len(classes), freeze_base=True)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    tf = build_transforms(image_size, train=False)

    picks = [(f, "def_front") for f in sample(TEST / "def_front", N_DEF)] + \
            [(f, "ok_front") for f in sample(TEST / "ok_front", N_OK)]
    # interleave so the log isn't all-fail-then-all-pass
    picks.sort(key=lambda x: x[0].name)

    base_time = datetime(2026, 7, 9, 9, 0, tzinfo=timezone.utc)
    inspections = []
    correct = 0
    for i, (path, true_cls) in enumerate(picks):
        img = Image.open(path).convert("RGB")
        x = tf(img).unsqueeze(0)
        t0 = time.perf_counter()
        with torch.no_grad():
            probs = F.softmax(model(x), dim=1)[0]
        ms = (time.perf_counter() - t0) * 1000
        idx = int(probs.argmax())
        pred = classes[idx]
        conf = float(probs[idx])
        correct += (pred == true_cls)
        pass_fail = "pass" if pred == "ok_front" else "fail"
        part_id = f"P-{1001 + i}"
        inspections.append({
            "timestamp": (base_time + timedelta(minutes=7 * i)).isoformat(),
            "part_id": part_id,
            "pass_fail": pass_fail,
            "defect_type": pred,
            "confidence": round(conf, 4),
            "inference_ms": round(ms, 2),
            "alert_hi": generate_alert(pred, conf, part_id=part_id, language="hi"),
            "thumb_b64": thumb_b64(img),
        })

    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    events["generated_at"] = datetime.now(timezone.utc).isoformat()
    events["inspections"] = inspections

    n = len(inspections)
    passes = sum(1 for x in inspections if x["pass_fail"] == "pass")
    fails = n - passes
    avg_ms = round(sum(x["inference_ms"] for x in inspections) / n, 1)
    events["kpis"].update({
        "total_inspections": n,
        "pass_count": passes,
        "fail_count": fails,
        "pass_rate": round(passes / n, 4),
        "avg_inference_ms": avg_ms,
        "module1_test_accuracy": M1_MEAN_TEST_ACC,
        "demand_forecast_wape_pct": M4_WAPE,
    })

    EVENTS.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rebuilt {n} inspections ({passes} pass / {fails} fail) from corrected model.")
    print(f"Sampled-image accuracy this batch: {correct}/{n} = {correct/n*100:.1f}%")
    print(f"Avg CPU inference: {avg_ms} ms")


if __name__ == "__main__":
    main()
