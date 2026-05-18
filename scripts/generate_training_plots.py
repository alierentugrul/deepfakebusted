"""Generate training loss/accuracy plots from saved training logs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "results" / "logs"
PLOTS_DIR = ROOT / "results" / "plots"


def _dark_fig(figsize=(8, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1e1e3f")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.tick_params(colors="white")
    ax.grid(True, alpha=0.2, color="white")
    return fig, ax


def _pretty_name(stem: str) -> str:
    if stem == "xception_hfdf40":
        return "Xception + DF40"
    return stem.replace("_", " ").title()


def _save_curve(
    epochs: list[int],
    train_values: list[float],
    val_values: list[float],
    *,
    ylabel: str,
    title: str,
    out_path: Path,
) -> None:
    fig, ax = _dark_fig()
    ax.plot(epochs, train_values, marker="o", color="#22c55e", lw=2.2, label="Train")
    ax.plot(epochs, val_values, marker="o", color="#f97316", lw=2.2, label="Validation")
    ax.set_xlabel("Epoch", color="white", fontsize=12)
    ax.set_ylabel(ylabel, color="white", fontsize=12)
    ax.set_title(title, color="white", fontsize=14, pad=12)
    ax.legend(loc="best", facecolor="#1a1a2e", edgecolor="grey", labelcolor="white")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_for_log(log_path: Path) -> None:
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    history = payload.get("epochs", [])
    if not history:
        return

    stem = log_path.stem.replace("_training", "")
    epochs = [row["epoch"] for row in history]
    train_loss = [row["train_loss"] for row in history]
    val_loss = [row["val_loss"] for row in history]
    train_acc = [row["train_acc"] for row in history]
    val_acc = [row["val_acc"] for row in history]
    display_name = _pretty_name(stem)

    _save_curve(
        epochs,
        train_loss,
        val_loss,
        ylabel="Loss",
        title=f"Training Loss — {display_name}",
        out_path=PLOTS_DIR / f"{stem}_loss_curve.png",
    )
    _save_curve(
        epochs,
        train_acc,
        val_acc,
        ylabel="Accuracy",
        title=f"Training Accuracy — {display_name}",
        out_path=PLOTS_DIR / f"{stem}_accuracy_curve.png",
    )


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    for log_path in sorted(LOGS_DIR.glob("*_training.json")):
        generate_for_log(log_path)
        print(f"generated plots for {log_path.stem.replace('_training', '')}")


if __name__ == "__main__":
    main()
