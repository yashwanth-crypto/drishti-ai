"""Baseline architectures for the casting defect classifier, so the
MobileNetV2 result can be compared against a stronger transfer-learning
model (ResNet-50) and a from-scratch small CNN (to show that transfer
learning actually helps, not just capacity).

All three are trained and evaluated on the SAME train/val/test split
(dataset.get_train_val_test_loaders) for a fair comparison.
"""
import torch.nn as nn
from torchvision.models import ResNet50_Weights, resnet50


def build_resnet50(num_classes: int = 2, freeze_base: bool = True) -> nn.Module:
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    if freeze_base:
        for p in model.parameters():
            p.requires_grad = False
    model.fc = nn.Sequential(nn.Dropout(0.2), nn.Linear(model.fc.in_features, num_classes))
    return model


def unfreeze_resnet_top(model: nn.Module) -> None:
    """Unfreeze the last residual stage (layer4) for fine-tuning."""
    for p in model.layer4.parameters():
        p.requires_grad = True


class SimpleCNN(nn.Module):
    """A small 3-block CNN trained from scratch -- no ImageNet pretraining.
    Included as a lower bound: if this trails the pretrained models, it
    demonstrates the value of transfer learning on a modest dataset."""

    def __init__(self, num_classes: int = 2):
        super().__init__()
        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(),
                nn.Conv2d(cout, cout, 3, padding=1), nn.BatchNorm2d(cout), nn.ReLU(),
                nn.MaxPool2d(2),
            )
        self.features = nn.Sequential(block(3, 32), block(32, 64), block(64, 128))
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            nn.Dropout(0.3), nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.head(self.features(x))
