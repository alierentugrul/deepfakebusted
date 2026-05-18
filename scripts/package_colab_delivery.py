"""
Create a small delivery bundle for the Colab workflow:

    dist_colab_delivery/
        DeepFakeBusted_code.zip
        current_dataset.zip
        checkpoints/xception_best.pth

The code archive intentionally excludes bulky local-only folders such as `venv`
and `data`.
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DATASET_ROOT = PROJECT_ROOT / "data" / "raw" / "archive" / "real_vs_fake" / "real-vs-fake"
DEFAULT_CHECKPOINT = PROJECT_ROOT / "results" / "checkpoints" / "xception_best.pth"

EXCLUDED_TOP_LEVEL = {"venv", ".venv", "data", "results", "__pycache__", "dist_colab_delivery"}
EXCLUDED_PARTS = {"node_modules", "__pycache__"}


def should_include(path: Path) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    if rel.parts and rel.parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    return not any(part in EXCLUDED_PARTS for part in rel.parts)


def write_zip_from_tree(source_root: Path, zip_path: Path, base_arcname: str | None = None) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in source_root.rglob("*"):
            if not path.is_file():
                continue
            if source_root == PROJECT_ROOT and not should_include(path):
                continue
            rel = path.relative_to(source_root)
            arcname = Path(base_arcname) / rel if base_arcname else rel
            zf.write(path, arcname.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Colab delivery artifacts")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "dist_colab_delivery"))
    parser.add_argument("--dataset-root", default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    dataset_root = Path(args.dataset_root)
    checkpoint = Path(args.checkpoint)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "checkpoints").mkdir(exist_ok=True)

    code_zip = output_dir / "DeepFakeBusted_code.zip"
    data_zip = output_dir / "current_dataset.zip"
    checkpoint_out = output_dir / "checkpoints" / checkpoint.name

    print(f"Writing code archive -> {code_zip}")
    write_zip_from_tree(PROJECT_ROOT, code_zip, base_arcname="DeepFakeBusted")

    print(f"Writing dataset archive -> {data_zip}")
    write_zip_from_tree(dataset_root, data_zip, base_arcname="real-vs-fake")

    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")
    shutil.copy2(checkpoint, checkpoint_out)
    print(f"Copied checkpoint -> {checkpoint_out}")
    print("Done.")


if __name__ == "__main__":
    main()
