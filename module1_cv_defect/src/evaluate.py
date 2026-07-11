"""Evaluate a trained checkpoint on the held-out test split.

Usage:
    python src/evaluate.py --checkpoint models/casting_mobilenetv2.pt --data-root data/casting
"""
import argparse

import torch
from sklearn.metrics import classification_report, confusion_matrix

from dataset import get_dataloaders
from model import build_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="models/casting_mobilenetv2.pt")
    parser.add_argument("--data-root", default="data/casting")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=4)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt = torch.load(args.checkpoint, map_location=device)
    classes = ckpt["classes"]
    image_size = ckpt["image_size"]

    _, test_loader, _ = get_dataloaders(
        args.data_root, image_size, args.batch_size, args.num_workers
    )

    model = build_model(num_classes=len(classes), freeze_base=True).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    print(f"Checkpoint reported val_acc during training: {ckpt['val_acc']:.4f}")
    print(f"Classes (index order): {classes}\n")

    print("Classification report:")
    print(classification_report(all_labels, all_preds, target_names=classes, digits=4))

    print("Confusion matrix (rows=true, cols=predicted):")
    cm = confusion_matrix(all_labels, all_preds)
    print(cm)


if __name__ == "__main__":
    main()
