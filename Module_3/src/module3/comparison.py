"""Canonical spatial-vs-Fourier comparison pipeline."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from module3.fourier import fourier_filter_gray
from module3.metrics import ErrorMetrics, compute_error_metrics
from module3.spatial import apply_filter2d_gray


@dataclass(frozen=True)
class ComparisonResult:
    """Outputs needed for visual and numerical validation."""

    original: np.ndarray
    spatial: np.ndarray
    fourier: np.ndarray
    difference: np.ndarray
    metrics: ErrorMetrics
    max_imaginary_abs: float


def compare_spatial_fourier(image_gray: np.ndarray, kernel: np.ndarray) -> ComparisonResult:
    """Run the matched zero-boundary spatial and Fourier paths.

    Args:
        image_gray: Single-channel image.
        kernel: Odd-sized blur kernel.

    Returns:
        Original image, both outputs, absolute difference image, and metrics.
    """
    original = np.asarray(image_gray, dtype=np.float64)
    spatial = apply_filter2d_gray(original, kernel, border_type=cv2.BORDER_CONSTANT)
    fourier_result = fourier_filter_gray(original, kernel)
    difference = np.abs(spatial - fourier_result.image)
    metrics = compute_error_metrics(spatial, fourier_result.image)
    return ComparisonResult(
        original=original,
        spatial=spatial,
        fourier=fourier_result.image,
        difference=difference,
        metrics=metrics,
        max_imaginary_abs=fourier_result.max_imaginary_abs,
    )
