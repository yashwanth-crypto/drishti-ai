"""Single-image inference and ONNX export for the casting defect classifier.

Usage:
    python src/infer.py predict --checkpoint models/casting_mobilenetv2.pt --image path/to/part.jpg
    python src/infer.py export  --checkpoint models/casting_mobilenetv2.pt --out models/casting_mobilenetv2.onnx
"""
import argparse
import json
import time

import torch
import torch.nn.functional as F
from PIL import Image

from dataset import build_transforms
from model import build_model


def load_checkpoint(checkpoint_path: str, device: torch.device):
    ckpt = torch.load(checkpoint_path, map_location=device)
    model = build_model(num_classes=len(ckpt["classes"]), freeze_base=True).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model, ckpt["classes"], ckpt["image_size"]


def predict(checkpoint: str, image_path: str) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, image_size = load_checkpoint(checkpoint, device)

    transform = build_transforms(image_size, train=False)
    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    start = time.time()
    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)[0]
    elapsed_ms = (time.time() - start) * 1000

    pred_idx = int(probs.argmax().item())
    defect_type = classes[pred_idx]
    pass_fail = "pass" if defect_type == "ok_front" else "fail"

    result = {
        "pass_fail": pass_fail,
        "defect_type": defect_type,
        "confidence": round(float(probs[pred_idx].item()), 4),
        "inference_ms": round(elapsed_ms, 2),
    }
    return result


def export_onnx(checkpoint: str, out_path: str):
    device = torch.device("cpu")
    model, classes, image_size = load_checkpoint(checkpoint, device)

    dummy_input = torch.randn(1, 3, image_size, image_size)
    # dynamo=False uses the stable TorchScript-based exporter. torch 2.11
    # defaults to the newer dynamo exporter, which failed on this model;
    # the legacy path writes a single self-contained .onnx reliably.
    torch.onnx.export(
        model,
        dummy_input,
        out_path,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )
    print(f"Exported ONNX model to {out_path}")
    print(f"Classes (index order): {classes}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict_parser = subparsers.add_parser("predict")
    predict_parser.add_argument("--checkpoint", default="models/casting_mobilenetv2.pt")
    predict_parser.add_argument("--image", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--checkpoint", default="models/casting_mobilenetv2.pt")
    export_parser.add_argument("--out", default="models/casting_mobilenetv2.onnx")

    args = parser.parse_args()

    if args.command == "predict":
        result = predict(args.checkpoint, args.image)
        print(json.dumps(result, indent=2))
    elif args.command == "export":
        export_onnx(args.checkpoint, args.out)


if __name__ == "__main__":
    main()
