"""
Prepare the Kaggle '140k Real and Fake Faces' dataset.

Kaggle dataset directory layout (after unzipping):
    real-vs-fake/
        train/
            real/   *.jpg
            fake/   *.jpg
        test/
            real/
            fake/

Output layout expected by training pipeline:
    data/processed/
        train/  real/  fake/
        valid/  real/  fake/
        test/   real/  fake/

Usage (from project root):
    python scripts/prepare_data.py --source data/raw/real-vs-fake
    python scripts/prepare_data.py --source data/raw/real-vs-fake --val-ratio 0.15 --max-per-class 30000
"""

import argparse
import random
import shutil
import sys
from pathlib import Path

from tqdm import tqdm


def prepare(source_dir: str, dest_dir: str, val_ratio: float = 0.15,
            max_per_class: int = 0, seed: int = 42):
    """
    Split the kaggle train fold into train + val, copy kaggle test as-is.

    Args:
        source_dir:    Root of the unzipped kaggle dataset.
        dest_dir:      Destination (data/processed/).
        val_ratio:     Fraction of kaggle train to use as validation.
        max_per_class: If > 0, cap images per class per split (useful for quick tests).
        seed:          Random seed for reproducibility.
    """
    random.seed(seed)
    source = Path(source_dir)
    dest   = Path(dest_dir)

    # Verify source structure
    for split in ["train", "test"]:
        for cls in ["real", "fake"]:
            p = source / split / cls
            if not p.exists():
                sys.exit(f"[ERROR] Expected directory not found: {p}\n"
                         f"  Check --source path. Got: {source}")

    # Create output directories
    for split in ["train", "valid", "test"]:
        for cls in ["real", "fake"]:
            (dest / split / cls).mkdir(parents=True, exist_ok=True)

    print(f"\nSource : {source}")
    print(f"Dest   : {dest}")
    print(f"Val %  : {val_ratio*100:.0f}%")
    if max_per_class:
        print(f"Cap    : {max_per_class:,} images/class/split")
    print()

    # ── Copy test set ────────────────────────────────────────────────────────
    print("── Copying test set ──────────────────────────────────────────")
    for cls in ["real", "fake"]:
        files = sorted((source / "test" / cls).glob("*.jpg"))
        if max_per_class:
            files = files[:max_per_class]
        for f in tqdm(files, desc=f"  test/{cls}", leave=False):
            shutil.copy2(f, dest / "test" / cls / f.name)
        print(f"  test/{cls}: {len(files):,}")

    # ── Split kaggle train → train + valid ───────────────────────────────────
    print("\n── Splitting train → train + valid ───────────────────────────")
    for cls in ["real", "fake"]:
        files = sorted((source / "train" / cls).glob("*.jpg"))
        random.shuffle(files)

        if max_per_class:
            files = files[:max_per_class]

        n_val        = int(len(files) * val_ratio)
        val_files    = files[:n_val]
        train_files  = files[n_val:]

        for f in tqdm(train_files, desc=f"  train/{cls}", leave=False):
            shutil.copy2(f, dest / "train" / cls / f.name)
        for f in tqdm(val_files,   desc=f"  valid/{cls}", leave=False):
            shutil.copy2(f, dest / "valid" / cls / f.name)

        print(f"  {cls}: {len(train_files):,} train  |  {len(val_files):,} valid")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n✅ Dataset ready!\n")
    total = 0
    for split in ["train", "valid", "test"]:
        for cls in ["real", "fake"]:
            n = len(list((dest / split / cls).glob("*")))
            total += n
            print(f"  {split:5s}/{cls}: {n:,}")
    print(f"\n  Grand total: {total:,} images")
    print(f"  Location   : {dest}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare 140k Real vs Fake dataset for DeepFakeBusted"
    )
    parser.add_argument("--source",        required=True, help="Path to extracted kaggle dataset root")
    parser.add_argument("--dest",          default="data/processed", help="Output directory")
    parser.add_argument("--val-ratio",     type=float, default=0.15, help="Validation split ratio")
    parser.add_argument("--max-per-class", type=int,   default=0,
                        help="Cap images per class (0 = no cap). Useful for quick smoke-tests.")
    args = parser.parse_args()

    prepare(args.source, args.dest, args.val_ratio, args.max_per_class)
