"""
Model factory — creates any supported model by name.

Supported models:
    mesonet         — Meso4, built from scratch
    resnet50        — ImageNet pretrained, FC replaced
    efficientnet_b4 — timm, pretrained
    xception        — timm, pretrained
    vit_base        — ViT-B/16 via timm, pretrained
"""

import torch.nn as nn
import torchvision.models as tv_models
import timm

from models.mesonet import Meso4

# Human-readable display names
MODEL_DISPLAY_NAMES = {
    "mesonet":          "MesoNet",
    "resnet50":         "ResNet-50",
    "efficientnet_b4":  "EfficientNet-B4",
    "xception":         "Xception",
    "xception_hfdf40":  "Xception + DF40 Dış Veri",
    "vit_base":         "ViT-B/16",
}


# SUNUM-ANAHTAR: model factory - MesoNet, ResNet50, EfficientNet, Xception ve ViT tek yerden seciliyor.
def get_model(model_name: str, num_classes: int = 2, pretrained: bool = True) -> nn.Module:
    """
    Create and return a model by name.

    Args:
        model_name:  One of the keys in MODEL_DISPLAY_NAMES.
        num_classes: Output dimension (2 for binary deepfake detection).
        pretrained:  Load ImageNet pretrained weights (ignored for MesoNet).

    Returns:
        Initialised PyTorch model (not moved to device yet).
    """
    name = model_name.lower().strip()

    if name == "mesonet":
        return Meso4(num_classes=num_classes)

    elif name == "resnet50":
        weights = tv_models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        model = tv_models.resnet50(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    elif name == "efficientnet_b4":
        return timm.create_model("efficientnet_b4", pretrained=pretrained, num_classes=num_classes)

    elif name in {"xception", "xception_hfdf40"}:
        return timm.create_model("xception", pretrained=pretrained, num_classes=num_classes)

    elif name == "vit_base":
        return timm.create_model("vit_base_patch16_224", pretrained=pretrained, num_classes=num_classes)

    else:
        supported = list(MODEL_DISPLAY_NAMES.keys())
        raise ValueError(f"Unknown model '{model_name}'. Supported: {supported}")


def count_parameters(model: nn.Module) -> dict:
    """Return total and trainable parameter counts."""
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable}


def get_model_size_mb(model: nn.Module) -> float:
    """Return approximate model size in megabytes."""
    param_bytes  = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_bytes = sum(b.numel() * b.element_size() for b in model.buffers())
    return (param_bytes + buffer_bytes) / (1024 ** 2)
