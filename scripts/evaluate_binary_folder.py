"""
Evaluate one checkpoint on a labeled binary folder:

    folder/
        real/
        fake/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from training.config import TRAIN_CONFIG
from training.dataset import DeepfakeDataset, get_transforms
from training.evaluate import get_predictions, load_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a checkpoint on folder/{real,fake}")
    parser.add_argument("--model", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output-json", default=None)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = TRAIN_CONFIG["mixed_precision"] and device.type == "cuda"

    dataset = DeepfakeDataset(args.data_dir, transform=get_transforms("valid", TRAIN_CONFIG["image_size"]))
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=TRAIN_CONFIG["num_workers"],
        pin_memory=TRAIN_CONFIG["pin_memory"],
    )
    model = load_model(args.model, device, run_name=args.run_name)
    labels, preds, probs = get_predictions(model, loader, device, use_amp)

    metrics = {
        "model": args.model,
        "run_name": args.run_name,
        "samples": int(len(labels)),
        "accuracy": round(float(accuracy_score(labels, preds)), 6),
        "auc_roc": round(float(roc_auc_score(labels, probs)), 6),
        "f1_score": round(float(f1_score(labels, preds, average="binary", zero_division=0)), 6),
        "precision": round(float(precision_score(labels, preds, average="binary", zero_division=0)), 6),
        "recall": round(float(recall_score(labels, preds, average="binary", zero_division=0)), 6),
        "confusion_matrix": confusion_matrix(labels, preds).tolist(),
        "fake_probability_mean": round(float(np.mean(probs)), 6),
    }

    print(json.dumps(metrics, indent=2))
    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"Saved metrics to: {out}")


if __name__ == "__main__":
    main()
