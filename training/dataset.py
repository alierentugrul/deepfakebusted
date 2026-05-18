"""
Dataset and DataLoader utilities for DeepFakeBusted.

Kaggle archive klasör yapısı (data/raw/archive/real_vs_fake/real-vs-fake/):
    train/
        real/   *.jpg
        fake/
    valid/
        real/
        fake/
    test/
        real/
        fake/
"""

from pathlib import Path
from typing import List, Optional, Tuple
import warnings

import torch
from torch.utils.data import ConcatDataset, DataLoader, Dataset
from torchvision import transforms
from PIL import Image

from training.config import (
    CLASS_TO_IDX,
    PROCESSED_DATA_DIR,
    TRAIN_CONFIG,
)

# ImageNet normalisation constants
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]


# SUNUM-ANAHTAR: data augmentation pipeline - train/valid/test image preprocessing burada.
def get_transforms(split: str, image_size: int = 224) -> transforms.Compose:
    """
    Return augmentation pipeline for the requested split.

    Training:   random crop, flip, colour jitter
    Val / Test: deterministic resize + centre crop
    """
    if split == "train":
        return transforms.Compose([
            transforms.Resize((image_size + 32, image_size + 32)),
            transforms.RandomCrop(image_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2,
                                   saturation=0.1, hue=0.05),
            transforms.RandomGrayscale(p=0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])


# SUNUM-ANAHTAR: dataset loader - real/fake klasorlerinden ornekleri ve etiketleri burada topluyorum.
class DeepfakeDataset(Dataset):
    """
    Binary deepfake image dataset.

    Loads all .jpg / .jpeg / .png images from:
        root_dir/real/
        root_dir/fake/
    """

    def __init__(
        self,
        root_dir: str,
        transform: Optional[transforms.Compose] = None,
    ):
        self.root_dir  = Path(root_dir)
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []

        for class_name, class_idx in CLASS_TO_IDX.items():
            class_dir = self.root_dir / class_name
            if not class_dir.exists():
                raise FileNotFoundError(
                    f"Klasör bulunamadı: {class_dir}\n"
                    f"  Beklenen yapı: data/raw/archive/real_vs_fake/real-vs-fake/{{train,valid,test}}/{{real,fake}}/"
                )
            image_files = (
                list(class_dir.glob("*.jpg"))
                + list(class_dir.glob("*.jpeg"))
                + list(class_dir.glob("*.png"))
            )
            for path in image_files:
                self.samples.append((path, class_idx))

        real_count = sum(1 for _, lbl in self.samples if lbl == CLASS_TO_IDX["real"])
        fake_count = sum(1 for _, lbl in self.samples if lbl == CLASS_TO_IDX["fake"])
        print(f"  [{self.root_dir.name}] real={real_count:,}  fake={fake_count:,}  total={len(self.samples):,}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as exc:
            # Fallback: grey square for corrupt images
            warnings.warn(f"Could not read image {img_path}: {exc}", RuntimeWarning, stacklevel=2)
            image = Image.new("RGB", (224, 224), (128, 128, 128))

        if self.transform:
            image = self.transform(image)

        return image, label


# SUNUM-ANAHTAR: dataloader pipeline - train/valid/test DataLoader nesneleri burada kuruluyor.
def _split_dir(root: Path, split: str) -> Path:
    if split == "valid":
        valid_dir = root / "valid"
        if not valid_dir.exists() and (root / "val").exists():
            return root / "val"
        return valid_dir
    return root / split


def _build_split_dataset(root: Path, split: str, image_size: int) -> DeepfakeDataset:
    transform_name = "train" if split == "train" else "valid"
    return DeepfakeDataset(
        _split_dir(root, split),
        transform=get_transforms(transform_name, image_size),
    )


def get_dataloaders(
    data_dir: str   = str(PROCESSED_DATA_DIR),
    image_size: int = TRAIN_CONFIG["image_size"],
    batch_size: int = 32,
    num_workers: int = TRAIN_CONFIG["num_workers"],
    pin_memory: bool = TRAIN_CONFIG["pin_memory"],
    extra_data_dirs: Optional[List[str]] = None,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Build train / val / test DataLoaders.

    Returns:
        (train_loader, val_loader, test_loader)
    """
    data_dir = Path(data_dir)

    print("Building datasets...")
    train_parts = [_build_split_dataset(data_dir, "train", image_size)]
    val_parts   = [_build_split_dataset(data_dir, "valid", image_size)]
    test_parts  = [_build_split_dataset(data_dir, "test", image_size)]

    for extra_dir in extra_data_dirs or []:
        extra_root = Path(extra_dir)
        print(f"Adding extra dataset root: {extra_root}")
        train_parts.append(_build_split_dataset(extra_root, "train", image_size))
        val_parts.append(_build_split_dataset(extra_root, "valid", image_size))
        test_parts.append(_build_split_dataset(extra_root, "test", image_size))

    train_ds = train_parts[0] if len(train_parts) == 1 else ConcatDataset(train_parts)
    val_ds   = val_parts[0]   if len(val_parts)   == 1 else ConcatDataset(val_parts)
    test_ds  = test_parts[0]  if len(test_parts)  == 1 else ConcatDataset(test_parts)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=pin_memory, drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=pin_memory,
    )

    return train_loader, val_loader, test_loader
