"""Dataset loading for the casting defect classification task (pass/fail)."""
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transforms(image_size: int = 224, train: bool = True) -> transforms.Compose:
    if train:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def get_dataloaders(
    data_root: str | Path,
    image_size: int = 224,
    batch_size: int = 32,
    num_workers: int = 4,
) -> tuple[DataLoader, DataLoader, list[str]]:
    """Expects data_root/train/{ok_front,def_front} and data_root/test/{ok_front,def_front}."""
    data_root = Path(data_root)

    train_dataset = datasets.ImageFolder(
        data_root / "train", transform=build_transforms(image_size, train=True)
    )
    test_dataset = datasets.ImageFolder(
        data_root / "test", transform=build_transforms(image_size, train=False)
    )

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )

    return train_loader, test_loader, train_dataset.classes


def get_train_val_test_loaders(
    data_root: str | Path,
    image_size: int = 224,
    batch_size: int = 32,
    num_workers: int = 4,
    val_frac: float = 0.15,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader, DataLoader, list[str]]:
    """Proper 3-way split for honest model selection.

    The original get_dataloaders() used the TEST folder as the validation
    set and saved the checkpoint with the best test accuracy -- i.e. the
    model was selected on the test set, which optimistically biases the
    reported number. This function instead carves a stratified VALIDATION
    subset out of the training folder (model selection happens here) and
    leaves the test folder completely untouched until the final, single
    evaluation. Two ImageFolder views of the same train directory are used
    so the train subset gets augmentation while the val subset uses the
    clean eval transform, without physically moving any files.
    """
    data_root = Path(data_root)

    train_full = datasets.ImageFolder(
        data_root / "train", transform=build_transforms(image_size, train=True)
    )
    val_full = datasets.ImageFolder(
        data_root / "train", transform=build_transforms(image_size, train=False)
    )
    test_dataset = datasets.ImageFolder(
        data_root / "test", transform=build_transforms(image_size, train=False)
    )

    indices = np.arange(len(train_full.targets))
    train_idx, val_idx = train_test_split(
        indices, test_size=val_frac, stratify=train_full.targets, random_state=seed
    )
    train_dataset = Subset(train_full, train_idx)
    val_dataset = Subset(val_full, val_idx)

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )

    return train_loader, val_loader, test_loader, train_full.classes
