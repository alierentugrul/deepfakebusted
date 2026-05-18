"""
Evaluation script for trained DeepFakeBusted models.

Usage (from project root):
    python -m training.evaluate --model resnet50
    python -m training.evaluate --model all
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

# SUNUM-ANAHTAR: terminal encoding - Windows cp1254 karakter hatalarini engeller.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")          # headless backend — no display needed
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix, roc_curve,
)
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_factory import get_model, get_model_size_mb
from training.dataset import get_dataloaders
from training.config import (
    TRAIN_CONFIG, MODEL_CONFIGS,
    CHECKPOINTS_DIR, METRICS_DIR, PLOTS_DIR,
    PROCESSED_DATA_DIR, IDX_TO_CLASS,
)


# ── Load checkpoint ────────────────────────────────────────────────────────────
def _artifact_stem(model_name: str, run_name: str | None = None) -> str:
    return model_name if not run_name else f"{model_name}_{run_name}"


def load_model(model_name: str, device: torch.device, run_name: str | None = None) -> torch.nn.Module:
    ckpt_path = CHECKPOINTS_DIR / f"{_artifact_stem(model_name, run_name)}_best.pth"
    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"No checkpoint at {ckpt_path}\n"
            f"Train the model first:  python -m training.train --model {model_name}"
        )
    model = get_model(model_name).to(device)
    ckpt  = torch.load(ckpt_path, map_location=device, weights_only=True)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print(f"  Loaded epoch {ckpt.get('epoch','?')}  val_acc={ckpt.get('val_acc', '?'):.4f}")
    return model


# ── Collect predictions ────────────────────────────────────────────────────────
@torch.no_grad()
# SUNUM-ANAHTAR: inference pipeline - test setindeki tahminler ve fake olasiliklari burada toplanir.
def get_predictions(model, loader, device, use_amp):
    all_labels, all_preds, all_probs = [], [], []
    for images, labels in tqdm(loader, desc="  inference", dynamic_ncols=True):
        images = images.to(device, non_blocking=True)
        if use_amp:
            with torch.amp.autocast("cuda"):
                outputs = model(images)
        else:
            outputs = model(images)
        probs = torch.softmax(outputs, dim=1)
        preds = probs.argmax(dim=1)
        all_labels.extend(labels.numpy())
        all_preds.extend(preds.cpu().numpy())
        all_probs.extend(probs[:, 1].cpu().numpy())   # P(fake)
    return np.array(all_labels), np.array(all_preds), np.array(all_probs)


# ── Inference time (single image) ─────────────────────────────────────────────
def measure_inference_ms(model, device, image_size: int = 224, n: int = 100) -> float:
    dummy = torch.randn(1, 3, image_size, image_size).to(device)
    # warmup
    for _ in range(10):
        with torch.no_grad():
            model(dummy)
    if device.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(n):
        with torch.no_grad():
            model(dummy)
    if device.type == "cuda":
        torch.cuda.synchronize()
    return round((time.perf_counter() - t0) / n * 1000, 3)


# ── Plot helpers ───────────────────────────────────────────────────────────────
def _dark_fig(figsize=(8, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1e1e3f")
    return fig, ax


# SUNUM-ANAHTAR: confusion matrix - modelin real/fake hata dagilimi burada grafike donusur.
def save_confusion_matrix(cm, model_name: str, out: Path):
    fig, ax = _dark_fig()
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["Real", "Fake"], yticklabels=["Real", "Fake"],
        ax=ax, annot_kws={"size": 16}, cbar_kws={"shrink": 0.8},
    )
    ax.set_title(f"Confusion Matrix — {model_name}", color="white", fontsize=14, pad=12)
    ax.set_xlabel("Predicted", color="white", fontsize=12)
    ax.set_ylabel("Actual",    color="white", fontsize=12)
    ax.tick_params(colors="white")
    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


# SUNUM-ANAHTAR: ROC AUC - ROC curve ve AUC grafigi burada uretilir.
def save_roc_curve(labels, probs, model_name: str, auc: float, out: Path):
    fpr, tpr, _ = roc_curve(labels, probs)
    fig, ax = _dark_fig()
    ax.plot(fpr, tpr, color="#6366f1", lw=2.5, label=f"AUC = {auc:.4f}")
    ax.plot([0, 1], [0, 1], color="#888", lw=1.5, linestyle="--", label="Random")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    ax.set_xlabel("False Positive Rate", color="white", fontsize=12)
    ax.set_ylabel("True Positive Rate",  color="white", fontsize=12)
    ax.set_title(f"ROC Curve — {model_name}", color="white", fontsize=14, pad=12)
    ax.legend(loc="lower right", facecolor="#1a1a2e", edgecolor="grey",
              labelcolor="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Main evaluation ────────────────────────────────────────────────────────────
# SUNUM-ANAHTAR: evaluation metrics - accuracy, AUC, F1, precision, recall ve hiz burada hesaplanir.
def evaluate(
    model_name: str,
    data_dir: str = str(PROCESSED_DATA_DIR),
    run_name: str | None = None,
    extra_data_dirs: list[str] | None = None,
) -> dict:
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = TRAIN_CONFIG["mixed_precision"] and device.type == "cuda"
    cfg     = MODEL_CONFIGS[model_name]

    print(f"\n{'='*62}")
    print(f"  Evaluating: {model_name.upper()}   device={device}")
    print(f"{'='*62}")

    model = load_model(model_name, device, run_name=run_name)

    print("Loading test data...")
    _, _, test_loader = get_dataloaders(
        data_dir        = data_dir,
        batch_size      = cfg["batch_size"],
        extra_data_dirs = extra_data_dirs,
    )

    labels, preds, probs = get_predictions(model, test_loader, device, use_amp)

    accuracy  = accuracy_score(labels, preds)
    f1        = f1_score(labels, preds,      average="binary", zero_division=0)
    precision = precision_score(labels, preds, average="binary", zero_division=0)
    recall    = recall_score(labels, preds,   average="binary", zero_division=0)
    auc       = roc_auc_score(labels, probs)
    cm        = confusion_matrix(labels, preds)

    print("\nMeasuring inference time (100 runs)...")
    inf_ms  = measure_inference_ms(model, device)
    size_mb = get_model_size_mb(model)

    metrics = {
        "model_name":     model_name,
        "accuracy":       round(accuracy,  6),
        "auc_roc":        round(auc,       6),
        "f1_score":       round(f1,        6),
        "precision":      round(precision, 6),
        "recall":         round(recall,    6),
        "confusion_matrix": cm.tolist(),
        "inference_ms":   inf_ms,
        "model_size_mb":  round(size_mb, 2),
        "test_samples":   int(len(labels)),
    }

    print(f"\n  Accuracy  : {accuracy:.4f}  ({accuracy*100:.2f} %)")
    print(f"  AUC-ROC   : {auc:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"  Precision : {precision:.4f}")
    print(f"  Recall    : {recall:.4f}")
    print(f"  Inf. Time : {inf_ms:.1f} ms / image")
    print(f"  Model Size: {size_mb:.2f} MB")

    # Save metrics JSON
    artifact_stem = _artifact_stem(model_name, run_name)
    metrics_path = METRICS_DIR / f"{artifact_stem}_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Metrics -> {metrics_path}")

    # Save plots
    cm_path  = PLOTS_DIR / f"{artifact_stem}_confusion_matrix.png"
    roc_path = PLOTS_DIR / f"{artifact_stem}_roc_curve.png"
    save_confusion_matrix(cm, model_name, cm_path)
    save_roc_curve(labels, probs, model_name, auc, roc_path)
    print(f"  Plots   -> {PLOTS_DIR}")

    return metrics


# -- CLI -----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate DeepFakeBusted model(s)")
    parser.add_argument(
        "--model", required=True,
        choices=list(MODEL_CONFIGS.keys()) + ["all"],
        help="Model name, or 'all' to evaluate every trained model",
    )
    parser.add_argument(
        "--data-dir",
        default=str(PROCESSED_DATA_DIR),
        help="Dataset root containing train/valid/test class folders",
    )
    parser.add_argument(
        "--extra-data-dir",
        action="append",
        default=[],
        help="Additional dataset root containing train/valid/test class folders. Can be repeated.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Optional suffix used when loading checkpoints, e.g. ai20k -> xception_ai20k_best.pth",
    )
    args = parser.parse_args()

    if args.model == "all":
        all_results = {}
        for m in MODEL_CONFIGS:
            if (CHECKPOINTS_DIR / f"{_artifact_stem(m, args.run_name)}_best.pth").exists():
                all_results[m] = evaluate(
                    m,
                    data_dir=args.data_dir,
                    run_name=args.run_name,
                    extra_data_dirs=args.extra_data_dir,
                )
            else:
                print(f"  [skip] {m}: no checkpoint found")
        combined = METRICS_DIR / "all_models_comparison.json"
        with open(combined, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nCombined results → {combined}")
    else:
        evaluate(
            args.model,
            data_dir=args.data_dir,
            run_name=args.run_name,
            extra_data_dirs=args.extra_data_dir,
        )
