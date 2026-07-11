"""Grad-CAM saliency for the casting defect classifier (paper Figure 4).

Grad-CAM (Selvaraju et al., 2017) highlights the image regions that most
drove the network's decision. For a defect-detection model this is
important evidence that the network attends to the actual defect region,
not a background/lighting artefact -- a common failure mode reviewers ask
about. Produces a grid of sample test images with their saliency overlays.

Usage:
    python src/gradcam.py --n 4 --out reports/gradcam.png
"""
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dataset import IMAGENET_MEAN, IMAGENET_STD, build_transforms
from model import build_model


def gradcam_for(model, tensor, target_layer, class_idx):
    activations, gradients = {}, {}

    def fwd_hook(_, __, output):
        activations["value"] = output.detach()

    def bwd_hook(_, grad_in, grad_out):
        gradients["value"] = grad_out[0].detach()

    h1 = target_layer.register_forward_hook(fwd_hook)
    h2 = target_layer.register_full_backward_hook(bwd_hook)

    # The backbone is frozen (requires_grad=False), so unless the INPUT
    # requires grad, autograd prunes the backward pass before it reaches
    # this conv layer and the backward hook never fires. Forcing the input
    # to require grad makes the full backward graph run.
    tensor = tensor.clone().detach().requires_grad_(True)
    logits = model(tensor)
    if class_idx is None:
        class_idx = int(logits.argmax(1))
    model.zero_grad()
    logits[0, class_idx].backward()

    acts = activations["value"][0]         # C,H,W
    grads = gradients["value"][0]          # C,H,W
    weights = grads.mean(dim=(1, 2))       # C
    cam = F.relu((weights[:, None, None] * acts).sum(0))
    cam = cam / (cam.max() + 1e-8)
    h1.remove(); h2.remove()
    return cam.cpu().numpy(), class_idx, float(F.softmax(logits, 1)[0, class_idx])


def denorm(tensor):
    img = tensor[0].cpu().numpy().transpose(1, 2, 0)
    img = img * np.array(IMAGENET_STD) + np.array(IMAGENET_MEAN)
    return np.clip(img, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="models/casting_mobilenetv2_proper.pt")
    ap.add_argument("--data-root", default="data/casting")
    ap.add_argument("--n", type=int, default=4, help="images per class")
    ap.add_argument("--out", default="reports/gradcam.png")
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    classes = ckpt["classes"]
    model = build_model(num_classes=len(classes), freeze_base=True)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    target_layer = model.features[-1]  # last conv block

    tf = build_transforms(224, train=False)
    test_dir = Path(args.data_root) / "test"
    samples = []
    for cls in classes:
        files = sorted((test_dir / cls).glob("*.jpeg"))[: args.n]
        samples += [(f, cls) for f in files]

    cols = args.n
    rows = 2 * len(classes)  # each class: row of originals + row of overlays
    fig, axes = plt.subplots(len(classes) * 2, cols, figsize=(cols * 2.4, len(classes) * 2 * 2.4))

    for ci, cls in enumerate(classes):
        files = sorted((test_dir / cls).glob("*.jpeg"))[: args.n]
        for j, f in enumerate(files):
            img = Image.open(f).convert("RGB")
            x = tf(img).unsqueeze(0)
            cam, pred_idx, conf = gradcam_for(model, x, target_layer, class_idx=None)
            base = denorm(x)
            cam_up = np.array(Image.fromarray((cam * 255).astype(np.uint8)).resize((224, 224))) / 255.0

            ax_o = axes[ci * 2][j]
            ax_o.imshow(base); ax_o.axis("off")
            if j == 0:
                ax_o.set_ylabel(f"{cls}\noriginal", rotation=0, ha="right", va="center", fontsize=8)
            ax_h = axes[ci * 2 + 1][j]
            ax_h.imshow(base); ax_h.imshow(cam_up, cmap="jet", alpha=0.45); ax_h.axis("off")
            ax_h.set_title(f"pred={classes[pred_idx]} ({conf*100:.0f}%)", fontsize=7)

    plt.suptitle("Grad-CAM: where the model looks (jet overlay = decisive regions)", fontsize=10)
    plt.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out, dpi=200, bbox_inches="tight")
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
