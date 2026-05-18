"""
Split a binary image dataset laid out as:

    source/
        real/
        fake/

into:

    dest/
        train/{real,fake}
        valid/{real,fake}
        test/{real,fake}
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def iter_images(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]


def stable_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:10]
    return f"{digest}_{path.name}"


def place_file(src: Path, dst: Path, mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(src, dst)
    elif mode == "hardlink":
        os.link(src, dst)
    elif mode == "symlink":
        os.symlink(src, dst)
    else:
        raise ValueError(f"Unsupported mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split real/fake folders into train/valid/test")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--dest-dir", required=True)
    parser.add_argument("--valid-frac", type=float, default=0.10)
    parser.add_argument("--test-frac", type=float, default=0.10)
    parser.add_argument("--max-per-class", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=["copy", "hardlink", "symlink"], default="copy")
    parser.add_argument("--clear-dest", action="store_true")
    args = parser.parse_args()

    source = Path(args.source_dir)
    dest = Path(args.dest_dir)
    if args.valid_frac + args.test_frac >= 1:
        raise ValueError("valid_frac + test_frac must be < 1")

    if args.clear_dest and dest.exists():
        shutil.rmtree(dest)

    rng = random.Random(args.seed)
    summary: dict[str, dict[str, int]] = {}

    for label in ("real", "fake"):
        class_root = source / label
        if not class_root.exists():
            raise FileNotFoundError(f"Missing class folder: {class_root}")

        files = iter_images(class_root)
        rng.shuffle(files)
        if args.max_per_class is not None:
            files = files[: args.max_per_class]

        n_total = len(files)
        n_test = round(n_total * args.test_frac)
        n_valid = round(n_total * args.valid_frac)
        split_map = {
            "test": files[:n_test],
            "valid": files[n_test : n_test + n_valid],
            "train": files[n_test + n_valid :],
        }

        summary[label] = {}
        for split, split_files in split_map.items():
            for src in split_files:
                dst = dest / split / label / stable_name(src, class_root)
                place_file(src, dst, args.mode)
            summary[label][split] = len(split_files)

    print(f"Created split dataset at: {dest}")
    for label, counts in summary.items():
        print(f"{label}: train={counts['train']} valid={counts['valid']} test={counts['test']}")


if __name__ == "__main__":
    main()
