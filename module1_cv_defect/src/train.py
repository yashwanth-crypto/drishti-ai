"""Train the MobileNetV2 pass/fail classifier on the casting defect dataset.

Usage:
    python src/train.py --data-root data/casting --epochs 15
"""
import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from tqdm import tqdm

from dataset import get_dataloaders
from model import build_model, unfreeze_top_layers


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="data/casting")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine-tune-epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--fine-tune-lr", type=float, default=1e-5)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--out", default="models/casting_mobilenetv2.pt")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader, test_loader, classes = get_dataloaders(
        args.data_root, args.image_size, args.batch_size, args.num_workers
    )
    print(f"Classes (index order): {classes}")

    model = build_model(num_classes=len(classes), freeze_base=True).to(device)
    criterion = nn.CrossEntropyLoss()

    # Phase 1: train the classifier head only, base frozen
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr
    )

    best_acc = 0.0
    history = []
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def train_phase(num_epochs, phase_name):
        nonlocal best_acc
        for epoch in range(num_epochs):
            start = time.time()
            train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
            val_loss, val_acc = run_epoch(model, test_loader, criterion, optimizer, device, train=False)
            elapsed = time.time() - start

            print(
                f"[{phase_name}] epoch {epoch + 1}/{num_epochs} "
                f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
                f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} ({elapsed:.1f}s)"
            )
            history.append({
                "phase": phase_name, "epoch": epoch + 1,
                "train_loss": train_loss, "train_acc": train_acc,
                "val_loss": val_loss, "val_acc": val_acc,
            })

            if val_acc > best_acc:
                best_acc = val_acc
                torch.save({
                    "model_state_dict": model.state_dict(),
                    "classes": classes,
                    "image_size": args.image_size,
                    "val_acc": val_acc,
                }, out_path)
                print(f"  -> saved new best model (val_acc={val_acc:.4f}) to {out_path}")

    train_phase(args.epochs, "head")

    # Phase 2: unfreeze top feature blocks and fine-tune at a low LR
    if args.fine_tune_epochs > 0:
        unfreeze_top_layers(model, num_layers=20)
        optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()), lr=args.fine_tune_lr
        )
        train_phase(args.fine_tune_epochs, "fine_tune")

    history_path = out_path.parent / "training_history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Training complete. Best val_acc={best_acc:.4f}. History saved to {history_path}")


if __name__ == "__main__":
    main()
