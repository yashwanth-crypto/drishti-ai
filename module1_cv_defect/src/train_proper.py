"""Methodologically-correct trainer for the casting defect classifier.

Differences from the original train.py (which reviewers would flag):
  - Uses a proper TRAIN / VAL / TEST split. The model is selected on a
    validation set carved out of the training folder; the test folder is
    evaluated exactly ONCE, at the very end. The old script selected the
    checkpoint on the test set, optimistically biasing its 99.4% figure.
  - Seeds Python/NumPy/PyTorch so runs are reproducible and can be
    repeated across several seeds for mean +/- std reporting.
  - Saves the final held-out test metrics (accuracy, per-class
    precision/recall/F1, confusion matrix) to JSON for the paper.

Usage:
    python src/train_proper.py --seed 42 --out models/casting_mobilenetv2_proper.pt
"""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from tqdm import tqdm

from dataset import get_train_val_test_loaders
from model import build_model, unfreeze_top_layers


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train() if train else model.eval()
    total_loss, correct, total = 0.0, 0, 0
    torch.set_grad_enabled(train)
    for images, labels in tqdm(loader, leave=False):
        images, labels = images.to(device), labels.to(device)
        if train:
            optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        if train:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * images.size(0)
        correct += (outputs.argmax(dim=1) == labels).sum().item()
        total += images.size(0)
    torch.set_grad_enabled(True)
    return total_loss / total, correct / total


@torch.no_grad()
def collect_preds(model, loader, device):
    model.eval()
    preds, labels = [], []
    for images, y in loader:
        out = model(images.to(device))
        preds.extend(out.argmax(dim=1).cpu().tolist())
        labels.extend(y.tolist())
    return labels, preds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="data/casting")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine-tune-epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--fine-tune-lr", type=float, default=1e-5)
    parser.add_argument("--val-frac", type=float, default=0.15)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="models/casting_mobilenetv2_proper.pt")
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device} | seed: {args.seed}")

    train_loader, val_loader, test_loader, classes = get_train_val_test_loaders(
        args.data_root, args.image_size, args.batch_size, args.num_workers,
        val_frac=args.val_frac, seed=args.seed,
    )
    print(f"Classes: {classes}")
    print(f"Split sizes -> train: {len(train_loader.dataset)}  "
          f"val: {len(val_loader.dataset)}  test: {len(test_loader.dataset)}")

    model = build_model(num_classes=len(classes), freeze_base=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)

    best_val_acc, best_state, best_where = 0.0, None, None
    history = []
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def train_phase(num_epochs, phase_name):
        nonlocal best_val_acc, best_state, best_where
        for epoch in range(num_epochs):
            start = time.time()
            tr_loss, tr_acc = run_epoch(model, train_loader, criterion, optimizer, device, True)
            va_loss, va_acc = run_epoch(model, val_loader, criterion, optimizer, device, False)
            print(f"[{phase_name}] epoch {epoch+1}/{num_epochs} "
                  f"train_acc={tr_acc:.4f} val_acc={va_acc:.4f} ({time.time()-start:.1f}s)")
            history.append({"phase": phase_name, "epoch": epoch + 1,
                            "train_loss": tr_loss, "train_acc": tr_acc,
                            "val_loss": va_loss, "val_acc": va_acc})
            # selection happens on VALIDATION, never on test
            if va_acc > best_val_acc:
                best_val_acc = va_acc
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                best_where = f"{phase_name} epoch {epoch+1}"

    train_phase(args.epochs, "head")
    if args.fine_tune_epochs > 0:
        unfreeze_top_layers(model, num_layers=20)
        optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.fine_tune_lr)
        train_phase(args.fine_tune_epochs, "fine_tune")

    # restore the best-on-validation weights, then touch the test set ONCE
    model.load_state_dict(best_state)
    print(f"\nBest model: {best_where} (val_acc={best_val_acc:.4f})")

    y_true, y_pred = collect_preds(model, test_loader, device)
    report = classification_report(y_true, y_pred, target_names=classes, digits=4, output_dict=True)
    cm = confusion_matrix(y_true, y_pred).tolist()
    test_acc = report["accuracy"]

    print("\n=== FINAL held-out TEST metrics (evaluated once) ===")
    print(classification_report(y_true, y_pred, target_names=classes, digits=4))
    print("Confusion matrix (rows=true, cols=pred):", cm)

    torch.save({"model_state_dict": best_state, "classes": classes,
                "image_size": args.image_size, "val_acc": best_val_acc,
                "test_acc": test_acc, "seed": args.seed}, out_path)

    metrics = {"seed": args.seed, "best_on": best_where, "val_acc": best_val_acc,
               "test_accuracy": test_acc, "test_report": report,
               "confusion_matrix": cm, "classes": classes, "history": history}
    with open(out_path.parent / f"proper_metrics_seed{args.seed}.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved model to {out_path} and metrics to proper_metrics_seed{args.seed}.json")


if __name__ == "__main__":
    main()
