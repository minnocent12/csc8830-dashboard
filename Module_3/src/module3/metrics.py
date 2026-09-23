"""Numerical comparison metrics for spatial vs. Fourier filtering."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ErrorMetrics:
    """Comparison values computed from two same-shaped images.

    Formulas use ``A`` as the spatial-domain output and ``B`` as the Fourier-domain output:

    ``MAE = mean(abs(A - B))``
    ``MSE = mean((A - B) ** 2)``
    ``RMSE = sqrt(MSE)``
    ``max_abs_error = max(abs(A - B))``
    ``PSNR = 20*log10(255) - 10*log10(MSE)``, with ``inf`` when ``MSE == 0``.
    """

    mae: float
    mse: float
    rmse: float
    max_abs_error: float
    psnr_db: float


def compute_error_metrics(spatial: np.ndarray, fourier: np.ndarray, *, max_value: float = 255.0) -> ErrorMetrics:
    """Compute image-difference metrics without rounding to ``uint8`` first.

    Args:
        spatial: Spatial-domain result.
        fourier: Fourier-domain result.
        max_value: Nominal maximum image intensity used for PSNR.

    Returns:
        Error metrics.

    Raises:
        ValueError: if shapes differ or arrays contain non-finite values.
    """
    a = np.asarray(spatial, dtype=np.float64)
    b = np.asarray(fourier, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} != {b.shape}")
    if a.size == 0:
        raise ValueError("cannot compare empty arrays")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("arrays must contain finite values")
    diff = a - b
    abs_diff = np.abs(diff)
    mae = float(np.mean(abs_diff))
    mse = float(np.mean(diff**2))
    rmse = float(np.sqrt(mse))
    max_abs_error = float(np.max(abs_diff))
    psnr_db = float("inf") if mse == 0.0 else float(20 * np.log10(max_value) - 10 * np.log10(mse))
    return ErrorMetrics(mae, mse, rmse, max_abs_error, psnr_db)
