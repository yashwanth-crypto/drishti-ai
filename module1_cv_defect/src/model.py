"""MobileNetV2 transfer-learning model for pass/fail casting defect classification."""
import torch
import torch.nn as nn
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2


def build_model(num_classes: int = 2, freeze_base: bool = True) -> nn.Module:
    model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)

    if freeze_base:
        for param in model.features.parameters():
            param.requires_grad = False

    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.2),
        nn.Linear(in_features, num_classes),
    )

    return model


def unfreeze_top_layers(model: nn.Module, num_layers: int = 20) -> None:
    """Unfreeze the last `num_layers` feature blocks for fine-tuning."""
    feature_layers = list(model.features.children())
    for layer in feature_layers[-num_layers:]:
        for param in layer.parameters():
            param.requires_grad = True


if __name__ == "__main__":
    m = build_model()
    x = torch.randn(1, 3, 224, 224)
    out = m(x)
    print("Output shape:", out.shape)
