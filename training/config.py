"""
Project-wide configuration for DeepFakeBusted.
"""

from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent

DATA_DIR          = PROJECT_ROOT / "data"
RAW_DATA_DIR      = DATA_DIR / "raw"
# Kaggle archive'ı zaten train/valid/test olarak bölünmüş geldi,
# prepare_data.py çalıştırmaya gerek yok.
PROCESSED_DATA_DIR = RAW_DATA_DIR / "archive" / "real_vs_fake" / "real-vs-fake"

RESULTS_DIR      = PROJECT_ROOT / "results"
CHECKPOINTS_DIR  = RESULTS_DIR / "checkpoints"
LOGS_DIR         = RESULTS_DIR / "logs"
PLOTS_DIR        = RESULTS_DIR / "plots"
METRICS_DIR      = RESULTS_DIR / "metrics"

# Auto-create output directories (PROCESSED_DATA_DIR zaten var, oluşturma)
for _d in [CHECKPOINTS_DIR, LOGS_DIR, PLOTS_DIR, METRICS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ─── Labels ─────────────────────────────────────────────────────────────────────
CLASSES      = ["real", "fake"]
CLASS_TO_IDX = {"real": 0, "fake": 1}
IDX_TO_CLASS = {0: "real", 1: "fake"}

# ─── Global Training Settings ───────────────────────────────────────────────────
# SUNUM-ANAHTAR: hyperparameters - global image size, worker, seed ve mixed precision ayarlari.
TRAIN_CONFIG = {
    "device":           "cuda",   # Falls back to CPU automatically in train.py
    "image_size":       224,
    "num_classes":      2,
    "num_workers":      4,
    "pin_memory":       True,
    "mixed_precision":  True,     # torch.amp — saves ~30-40% VRAM on 3050 Ti
    "seed":             42,
}

# ─── Per-Model Hyperparameters ───────────────────────────────────────────────────
# Batch sizes tuned for RTX 3050 Ti (4 GB VRAM) with mixed precision enabled.
# SUNUM-ANAHTAR: model hyperparameters - her modelin batch size, learning rate, epoch ve early stopping ayari.
MODEL_CONFIGS = {
    "mesonet": {
        "batch_size":               64,
        "lr":                       1e-3,
        "weight_decay":             1e-4,
        "epochs":                   20,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
    "resnet50": {
        "batch_size":               32,
        "lr":                       1e-4,
        "weight_decay":             1e-4,
        "epochs":                   20,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
    "efficientnet_b4": {
        "batch_size":               16,
        "lr":                       5e-5,
        "weight_decay":             1e-4,
        "epochs":                   20,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
    "xception": {
        "batch_size":               16,
        "lr":                       5e-5,
        "weight_decay":             1e-4,
        "epochs":                   20,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
    "xception_hfdf40": {
        "batch_size":               16,
        "lr":                       5e-5,
        "weight_decay":             1e-4,
        "epochs":                   8,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
    "vit_base": {
        "batch_size":               8,
        "lr":                       1e-5,
        "weight_decay":             1e-4,
        "epochs":                   20,
        "scheduler":                "cosine",
        "early_stopping_patience":  5,
    },
}

# Models that should appear in the live demo dropdown.
# Experimental / auxiliary variants can live outside MODEL_CONFIGS when they
# reuse an existing architecture but have their own checkpoint file.
DEMO_MODELS = [
    "mesonet",
    "resnet50",
    "efficientnet_b4",
    "xception",
    "xception_hfdf40",
]
