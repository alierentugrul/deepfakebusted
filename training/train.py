"""
Training script for DeepFakeBusted.

Usage (from project root):
    python -m training.train --model mesonet
    python -m training.train --model resnet50
    python -m training.train --model efficientnet_b4
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

# Windows terminali UTF-8 olmayan durumlarda özel karakterleri basamaz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

# ── Project root on sys.path so imports always resolve ────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_factory import get_model, count_parameters, get_model_size_mb
from training.dataset import get_dataloaders
from training.config import (
    TRAIN_CONFIG, MODEL_CONFIGS,
    CHECKPOINTS_DIR, LOGS_DIR, PROCESSED_DATA_DIR,
)


# ── Reproducibility ────────────────────────────────────────────────────────────
def set_seed(seed: int = 42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ── One training epoch ─────────────────────────────────────────────────────────
# SUNUM-ANAHTAR: training loop - bir epoch icin forward/backward/optimizer adimlari burada.
def train_one_epoch(model, loader, optimizer, criterion, scaler, device, use_amp):
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    pbar = tqdm(loader, desc="  train", leave=False, dynamic_ncols=True)
    for images, labels in pbar:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        if use_amp:
            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss    = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss    = criterion(outputs, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        bs = images.size(0)
        total_loss += loss.item() * bs
        correct    += (outputs.argmax(1) == labels).sum().item()
        total      += bs

        pbar.set_postfix(loss=f"{loss.item():.4f}", acc=f"{correct/total:.4f}")

    return total_loss / total, correct / total


# ── Validation epoch ───────────────────────────────────────────────────────────
@torch.no_grad()
# SUNUM-ANAHTAR: validation pipeline - her epoch sonunda valid set performansi burada olculuyor.
def validate(model, loader, criterion, device, use_amp):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in tqdm(loader, desc="  val  ", leave=False, dynamic_ncols=True):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        if use_amp:
            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss    = criterion(outputs, labels)
        else:
            outputs = model(images)
            loss    = criterion(outputs, labels)

        bs = images.size(0)
        total_loss += loss.item() * bs
        correct    += (outputs.argmax(1) == labels).sum().item()
        total      += bs

    return total_loss / total, correct / total


# ── Main training routine ──────────────────────────────────────────────────────
# SUNUM-ANAHTAR: training pipeline - veri yukleme, model kurma, optimizer, scheduler, checkpoint ve log akisi burada.
def _artifact_stem(model_name: str, run_name: str | None = None) -> str:
    return model_name if not run_name else f"{model_name}_{run_name}"


def train(
    model_name: str,
    resume: bool = False,
    data_dir: str = str(PROCESSED_DATA_DIR),
    extra_data_dirs: list[str] | None = None,
    run_name: str | None = None,
    epochs_override: int | None = None,
    batch_size_override: int | None = None,
    lr_override: float | None = None,
):
    set_seed(TRAIN_CONFIG["seed"])

    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # SUNUM-ANAHTAR: mixed precision - GPU bellek kullanimini azaltip egitimi hizlandiriyor.
    use_amp = TRAIN_CONFIG["mixed_precision"] and device.type == "cuda"
    cfg     = MODEL_CONFIGS[model_name].copy()
    if epochs_override is not None:
        cfg["epochs"] = epochs_override
    if batch_size_override is not None:
        cfg["batch_size"] = batch_size_override
    if lr_override is not None:
        cfg["lr"] = lr_override

    # ── Banner ────────────────────────────────────────────────────────────────
    print(f"\n{'='*62}")
    print(f"  Model  : {model_name.upper()}")
    print(f"  Device : {device}" + (f"  [{torch.cuda.get_device_name(0)}]" if device.type == "cuda" else ""))
    print(f"  AMP    : {use_amp}")
    print(f"  Epochs : {cfg['epochs']}   Batch: {cfg['batch_size']}   LR: {cfg['lr']}")
    print(f"{'='*62}\n")

    # ── Data ──────────────────────────────────────────────────────────────────
    print("Loading data...")
    train_loader, val_loader, _ = get_dataloaders(
        data_dir        = data_dir,
        batch_size      = cfg["batch_size"],
        extra_data_dirs = extra_data_dirs,
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    print(f"\nBuilding model: {model_name}")
    model  = get_model(model_name).to(device)
    params = count_parameters(model)
    size   = get_model_size_mb(model)
    print(f"  {params['total']:,} params  |  {params['trainable']:,} trainable  |  {size:.2f} MB\n")

    # ── Training tools ────────────────────────────────────────────────────────
    # SUNUM-ANAHTAR: optimizer scheduler - AdamW + CosineAnnealingLR egitim stratejisi.
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    scheduler = CosineAnnealingLR(optimizer, T_max=cfg["epochs"], eta_min=cfg["lr"] * 0.01)
    scaler    = torch.amp.GradScaler("cuda", enabled=use_amp)

    best_val_loss = float("inf")
    patience      = 0
    start_epoch   = 1
    
    artifact_stem   = _artifact_stem(model_name, run_name)
    checkpoint_path = CHECKPOINTS_DIR / f"{artifact_stem}_best.pth"
    log_path        = LOGS_DIR        / f"{artifact_stem}_training.json"

    if resume and checkpoint_path.exists():
        print(f"\n[!] Resuming from checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_loss = checkpoint["val_loss"]
        print(f"    -> Starting from epoch {start_epoch} (Previous Best Val Loss: {best_val_loss:.4f})\n")

    history       = {
        "model_name": model_name,
        "params":     params,
        "size_mb":    round(size, 2),
        "config":     cfg,
        "device":     str(device),
        "run_name":   run_name,
        "data_dir":   data_dir,
        "extra_data_dirs": extra_data_dirs or [],
        "epochs":     [],
    }

    print(f"Training — {cfg['epochs']} epochs, early stop after {cfg['early_stopping_patience']} ...")
    wall_start = time.time()

    for epoch in range(start_epoch, cfg["epochs"] + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, optimizer, criterion, scaler, device, use_amp
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device, use_amp)
        scheduler.step()

        is_best = val_loss < best_val_loss
        flag    = " [*]" if is_best else ""
        elapsed = time.time() - t0

        print(
            f"Epoch [{epoch:03d}/{cfg['epochs']}]  "
            f"train loss={train_loss:.4f} acc={train_acc:.4f}  "
            f"val loss={val_loss:.4f} acc={val_acc:.4f}  "
            f"({elapsed:.1f}s){flag}"
        )

        history["epochs"].append({
            "epoch":      epoch,
            "train_loss": round(train_loss, 6),
            "train_acc":  round(train_acc,  6),
            "val_loss":   round(val_loss,   6),
            "val_acc":    round(val_acc,    6),
            "lr":         round(optimizer.param_groups[0]["lr"], 8),
            "epoch_time_s": round(elapsed, 2),
        })

        if is_best:
            best_val_loss = val_loss
            patience = 0
            torch.save({
                "epoch":             epoch,
                "model_name":        model_name,
                "model_state_dict":  model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "val_loss":          val_loss,
                "val_acc":           val_acc,
                "config":            cfg,
            }, checkpoint_path)
        else:
            patience += 1
            # SUNUM-ANAHTAR: early stopping - valid loss iyilesmezse egitimi erken durduruyor.
            if patience >= cfg["early_stopping_patience"]:
                print(f"\n  Early stopping triggered at epoch {epoch}.")
                break

        # Save log every epoch (safe even if interrupted)
        history["total_time_s"] = round(time.time() - wall_start, 2)
        with open(log_path, "w") as f:
            json.dump(history, f, indent=2)

    total_time = time.time() - wall_start
    history["total_time_s"]  = round(total_time, 2)
    history["best_val_loss"] = round(best_val_loss, 6)
    with open(log_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n{'='*62}")
    print(f"  Done!  {total_time/60:.1f} min  |  best val loss: {best_val_loss:.4f}")
    print(f"  Checkpoint : {checkpoint_path}")
    print(f"  Log        : {log_path}")
    print(f"{'='*62}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a DeepFakeBusted model")
    parser.add_argument(
        "--model", required=True,
        choices=list(MODEL_CONFIGS.keys()),
        help="Model name",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume training from the last saved checkpoint",
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
        help="Optional suffix for checkpoints/logs, e.g. ai20k -> xception_ai20k_best.pth",
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override configured epoch count")
    parser.add_argument("--batch-size", type=int, default=None, help="Override configured batch size")
    parser.add_argument("--lr", type=float, default=None, help="Override configured learning rate")
    args = parser.parse_args()
    train(
        args.model,
        resume=args.resume,
        data_dir=args.data_dir,
        extra_data_dirs=args.extra_data_dir,
        run_name=args.run_name,
        epochs_override=args.epochs,
        batch_size_override=args.batch_size,
        lr_override=args.lr,
    )
