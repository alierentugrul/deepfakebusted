"""
Export a Hugging Face image-classification dataset into:

    dest/
        real/
        fake/

The script tries to infer the image and label columns automatically, but also
accepts explicit labels if the dataset uses unusual naming.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

from PIL import Image


def _find_image_column(features: dict[str, Any]) -> str:
    for name, feature in features.items():
        if feature.__class__.__name__.lower() == "image":
            return name
    if "image" in features:
        return "image"
    raise ValueError("Could not infer image column; pass --image-column")


def _normalise_label(value: Any, label_names: list[str] | None) -> str:
    if isinstance(value, str):
        return value.lower()
    if label_names is not None:
        return label_names[int(value)].lower()
    return str(value).lower()


def _infer_targets(values: set[str], real_label: str | None, fake_label: str | None) -> tuple[str, str]:
    if real_label is not None and fake_label is not None:
        return real_label.lower(), fake_label.lower()

    real_candidates = [v for v in values if "real" in v or "authentic" in v or "genuine" in v]
    fake_candidates = [v for v in values if "fake" in v or "deepfake" in v or "synthetic" in v]
    if len(real_candidates) == 1 and len(fake_candidates) == 1:
        return real_candidates[0], fake_candidates[0]

    if values == {"0", "1"}:
        return "0", "1"

    raise ValueError(
        "Could not infer real/fake labels. "
        f"Observed labels: {sorted(values)}. Pass --real-label and --fake-label."
    )


def _save_image(image: Any, path: Path) -> None:
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    image.convert("RGB").save(path, format="JPEG", quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a Hugging Face binary face dataset")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--split", default="train")
    parser.add_argument("--dest-dir", required=True)
    parser.add_argument("--image-column", default=None)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--real-label", default=None)
    parser.add_argument("--fake-label", default=None)
    parser.add_argument("--max-per-class", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from datasets import load_dataset  # lazy import: only needed for this helper script

    ds = load_dataset(args.dataset_id, split=args.split)
    image_column = args.image_column or _find_image_column(ds.features)
    if args.label_column not in ds.features:
        raise ValueError(f"Label column not found: {args.label_column}")

    label_feature = ds.features[args.label_column]
    label_names = getattr(label_feature, "names", None)
    normalised_labels = [
        _normalise_label(row[args.label_column], label_names)
        for row in ds
    ]
    real_target, fake_target = _infer_targets(
        set(normalised_labels),
        args.real_label,
        args.fake_label,
    )

    buckets = {"real": [], "fake": []}
    for idx, label in enumerate(normalised_labels):
        if label == real_target:
            buckets["real"].append(idx)
        elif label == fake_target:
            buckets["fake"].append(idx)

    rng = random.Random(args.seed)
    dest = Path(args.dest_dir)
    for class_name, indices in buckets.items():
        rng.shuffle(indices)
        if args.max_per_class is not None:
            indices = indices[: args.max_per_class]
        class_dir = dest / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for out_idx, row_idx in enumerate(indices):
            row = ds[row_idx]
            _save_image(row[image_column], class_dir / f"{class_name}_{out_idx:06d}.jpg")
        print(f"{class_name}: exported {len(indices)} images")

    print(f"Exported dataset to: {dest}")


if __name__ == "__main__":
    main()
