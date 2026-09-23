"""Headless visualization helpers for reports and the Streamlit app."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from module3.comparison import ComparisonResult


def contrast_stretch(image: np.ndarray) -> np.ndarray:
    """Scale a difference image to 0-255 for visual inspection only."""
    array = np.asarray(image, dtype=np.float64)
    max_value = float(np.max(array)) if array.size else 0.0
    if max_value <= 0:
        return np.zeros_like(array, dtype=np.uint8)
    return np.clip(np.rint(array / max_value * 255), 0, 255).astype(np.uint8)


def save_comparison_figure(result: ComparisonResult, output_path: str | Path, *, title: str) -> None:
    """Save a four-panel original/spatial/Fourier/difference figure."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), constrained_layout=True)
    panels = [
        ("Original", result.original, "gray"),
        ("Spatial", result.spatial, "gray"),
        ("Fourier", result.fourier, "gray"),
        ("|Spatial - Fourier| (stretched)", contrast_stretch(result.difference), "magma"),
    ]
    for ax, (label, image, cmap) in zip(axes, panels):
        ax.imshow(image, cmap=cmap)
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def save_kernel_figure(kernel: np.ndarray, output_path: str | Path, *, title: str) -> None:
    """Save a heatmap of kernel values."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4, 4), constrained_layout=True)
    im = ax.imshow(kernel, cmap="viridis")
    ax.set_title(title)
    for y in range(kernel.shape[0]):
        for x in range(kernel.shape[1]):
            ax.text(x, y, f"{kernel[y, x]:.3f}", ha="center", va="center", color="white")
    fig.colorbar(im, ax=ax)
    fig.savefig(output, dpi=160)
    plt.close(fig)
