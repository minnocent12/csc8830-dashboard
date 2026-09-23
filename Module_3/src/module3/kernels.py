"""Explicit blur-kernel generation for the Module 3 filtering experiments."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

KernelArray = np.ndarray


@dataclass(frozen=True)
class KernelSpec:
    """A named blur kernel used by the spatial and Fourier paths."""

    filter_name: str
    size: int
    kernel: KernelArray
    sigma: float | None = None


def validate_odd_size(size: int) -> int:
    """Return a valid odd positive kernel size.

    Args:
        size: Candidate kernel width/height.

    Returns:
        ``size`` as an integer.

    Raises:
        ValueError: if ``size`` is non-positive or even.
    """
    size = int(size)
    if size <= 0:
        raise ValueError("kernel size must be positive")
    if size % 2 == 0:
        raise ValueError("kernel size must be odd")
    return size


def box_kernel(size: int) -> KernelArray:
    """Create a normalized square average/box kernel.

    Args:
        size: Odd positive kernel size.

    Returns:
        A ``float64`` kernel whose values sum to 1.
    """
    size = validate_odd_size(size)
    kernel = np.ones((size, size), dtype=np.float64)
    return kernel / kernel.sum()


def gaussian_kernel(size: int, sigma: float = 0.0) -> KernelArray:
    """Create a normalized square Gaussian kernel using OpenCV's convention.

    ``sigma=0`` delegates sigma selection to OpenCV, matching ``cv2.GaussianBlur`` for
    apples-to-apples cross-checks.

    Args:
        size: Odd positive kernel size.
        sigma: Gaussian standard deviation. ``0`` means OpenCV's default formula.

    Returns:
        A ``float64`` kernel whose values sum to 1.

    Raises:
        ValueError: if ``sigma`` is negative or non-finite.
    """
    size = validate_odd_size(size)
    sigma = float(sigma)
    if not np.isfinite(sigma) or sigma < 0:
        raise ValueError("sigma must be finite and non-negative")
    one_d = cv2.getGaussianKernel(size, sigma, ktype=cv2.CV_64F)
    kernel = one_d @ one_d.T
    return kernel / kernel.sum()


def make_kernel(filter_name: str, size: int, sigma: float = 0.0) -> KernelSpec:
    """Create a named kernel specification.

    Args:
        filter_name: ``"average"``/``"box"`` or ``"gaussian"``.
        size: Odd positive kernel size.
        sigma: Gaussian sigma, used only for Gaussian filters.

    Returns:
        A :class:`KernelSpec` with normalized ``float64`` kernel values.

    Raises:
        ValueError: if the filter name is unknown.
    """
    normalized = filter_name.strip().lower()
    if normalized in {"average", "avg", "box"}:
        return KernelSpec("Average Blur", validate_odd_size(size), box_kernel(size), None)
    if normalized in {"gaussian", "gaussian blur"}:
        return KernelSpec("Gaussian Blur", validate_odd_size(size), gaussian_kernel(size, sigma), sigma)
    raise ValueError(f"unknown filter type: {filter_name!r}")
