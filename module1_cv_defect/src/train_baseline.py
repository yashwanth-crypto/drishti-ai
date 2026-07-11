"""Train a baseline architecture (ResNet-50 or a from-scratch SimpleCNN)
on the same proper train/val/test split as the MobileNetV2 model, for a
fair paper comparison. Model selection on validation; test evaluated once.

Usage:
    python src/train_baseline.py --arch resnet50 --seed 42
    python src/train_baseline.py --arch simplecnn --seed 42 --epochs 20
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

from baselines import SimpleCNN, build_resnet50, unfreeze_resnet_top
from dataset import get_train_val_test_loaders


def set_seed(seed):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)


def run_epoch(model, loader, criterion, optimizer, device, train):
    model.train() if train else model.eval()
    total_loss, correct, total = 0.0, 0, 0
    torch.set_grad_enabled(train)
    for images, labels in tqdm(loader, leave=False):
        images, labels = images.to(device), labels.to(device)
        if train:
            optimizer.zero_grad()
        out = model(images)
        loss = criterion(out, labels)
        if train:
            loss.backward(); optimizer.step()
        total_loss += loss.item() * images.size(0)
        correct += (out.argmax(1) == labels).sum().item()
        total += images.size(0)
    torch.set_grad_enabled(True)
    return total_loss / total, correct / total


@torch.no_grad()
def collect(model, loader, device):
    model.eval(); preds, labels = [], []
    for images, y in loader:
        preds.extend(model(images.to(device)).argmax(1).cpu().tolist())
        labels.extend(y.tolist())
    return labels, preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", choices=["resnet50", "simplecnn"], required=True)
    ap.add_argument("--data-root", default="data/casting")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--fine-tune-epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--fine-tune-lr", type=float, default=1e-5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--num-workers", type=int, default=4)
    args = ap.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"arch={args.arch} device={device} seed={args.seed}")

    train_loader, val_loader, test_loader, classes = get_train_val_test_loaders(
        args.data_root, 224, args.batch_size, args.num_workers, seed=args.seed)
    print(f"split -> train {len(train_loader.dataset)} val {len(val_loader.dataset)} test {len(test_loader.dataset)}")

    pretrained = args.arch == "resnet50"
    if args.arch == "resnet50":
        model = build_resnet50(len(classes), freeze_base=True).to(device)
    else:
        model = SimpleCNN(len(classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)

    best_val, best_state, best_where = 0.0, None, None
    history = []

    def phase(n, name):
        nonlocal best_val, best_state, best_where
        for e in range(n):
            t = time.time()
            tl, ta = run_epoch(model, train_loader, criterion, optimizer, device, True)
            vl, va = run_epoch(model, val_loader, criterion, optimizer, device, False)
            print(f"[{name}] {e+1}/{n} train_acc={ta:.4f} val_acc={va:.4f} ({time.time()-t:.1f}s)")
            history.append({"phase": name, "epoch": e + 1, "train_acc": ta, "val_acc": va})
            if va > best_val:
                best_val = va
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                best_where = f"{name} epoch {e+1}"

    phase(args.epochs, "head" if pretrained else "scratch")
    if pretrained and args.fine_tune_epochs > 0:
        unfreeze_resnet_top(model)
        optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.fine_tune_lr)
        phase(args.fine_tune_epochs, "fine_tune")

    model.load_state_dict(best_state)
    y_true, y_pred = collect(model, test_loader, device)
    report = classification_report(y_true, y_pred, target_names=classes, digits=4, output_dict=True)
    cm = confusion_matrix(y_true, y_pred).tolist()
    print(f"\nBest: {best_where} (val_acc={best_val:.4f})")
    print("=== TEST ===")
    print(classification_report(y_true, y_pred, target_names=classes, digits=4))
    print("Confusion matrix:", cm)

    out = Path("models") / f"baseline_{args.arch}_metrics_seed{args.seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump({"arch": args.arch, "seed": args.seed, "val_acc": best_val,
                   "test_accuracy": report["accuracy"], "test_report": report,
                   "confusion_matrix": cm, "history": history}, f, indent=2)
    print(f"Saved metrics to {out}")


if __name__ == "__main__":
    main()
