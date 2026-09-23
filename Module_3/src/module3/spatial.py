"""Spatial-domain blur filtering with OpenCV.

OpenCV's ``filter2D`` computes correlation, not mathematical convolution. For the symmetric
box and Gaussian kernels used in this assignment, correlation equals convolution because
flipping the kernel does not change it. The test suite includes an asymmetric-kernel example
to document why this distinction matters if future kernels are added.

For color previews, OpenCV applies the same 2D kernel independently to each BGR channel.
The canonical comparison pipeline remains single-channel grayscale ``float64``.
"""
from __future__ import annotations

import cv2
import numpy as np

from module3.io_utils import ensure_gray_float64
from module3.kernels import KernelArray, gaussian_kernel, validate_odd_size


def validate_kernel(kernel: KernelArray) -> KernelArray:
    """Validate a finite odd-sized 2D kernel.

    Args:
        kernel: Candidate convolution kernel.

    Returns:
        ``kernel`` as ``float64``.

    Raises:
        ValueError: if the kernel is not a finite odd-sized 2D array.
    """
    result = np.asarray(kernel, dtype=np.float64)
    if result.ndim != 2:
        raise ValueError("kernel must be a 2D array")
    if result.shape[0] % 2 == 0 or result.shape[1] % 2 == 0:
        raise ValueError("kernel height and width must be odd")
    if result.shape[0] <= 0 or result.shape[1] <= 0:
        raise ValueError("kernel must be non-empty")
    if not np.all(np.isfinite(result)):
        raise ValueError("kernel contains non-finite values")
    return result


def apply_filter2d_gray(
    image: np.ndarray,
    kernel: KernelArray,
    *,
    border_type: int = cv2.BORDER_CONSTANT,
) -> np.ndarray:
    """Apply the explicit kernel to a grayscale image using ``cv2.filter2D``.

    Args:
        image: Single-channel image.
        kernel: Odd-sized blur kernel.
        border_type: OpenCV border mode. Use ``BORDER_CONSTANT`` for Fourier equivalence.

    Returns:
        Filtered ``float64`` image with the same shape as ``image``.
    """
    image_f64 = ensure_gray_float64(image)
    kernel_f64 = validate_kernel(kernel)
    return cv2.filter2D(image_f64, ddepth=-1, kernel=kernel_f64, borderType=border_type)


def apply_filter2d_bgr(
    image_bgr: np.ndarray,
    kernel: KernelArray,
    *,
    border_type: int = cv2.BORDER_REFLECT_101,
) -> np.ndarray:
    """Apply the same 2D kernel independently to each BGR channel.

    Args:
        image_bgr: BGR image with shape ``(height, width, 3)``.
        kernel: Odd-sized blur kernel.
        border_type: OpenCV border mode. Reflect is the display default.

    Returns:
        Filtered BGR image in ``float64``.

    Raises:
        ValueError: if the input is not a 3-channel image.
    """
    array = np.asarray(image_bgr)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("expected a BGR image with shape (height, width, 3)")
    return cv2.filter2D(array.astype(np.float64), ddepth=-1, kernel=validate_kernel(kernel), borderType=border_type)


def apply_average_blur_gray(
    image: np.ndarray,
    size: int,
    *,
    border_type: int = cv2.BORDER_CONSTANT,
) -> np.ndarray:
    """Apply OpenCV's average blur to grayscale data as a cross-check path."""
    size = validate_odd_size(size)
    image_f64 = ensure_gray_float64(image)
    return cv2.blur(image_f64, (size, size), borderType=border_type)


def apply_gaussian_blur_gray(
    image: np.ndarray,
    size: int,
    *,
    sigma: float = 0.0,
    border_type: int = cv2.BORDER_CONSTANT,
) -> np.ndarray:
    """Apply OpenCV's Gaussian blur to grayscale data as a cross-check path."""
    size = validate_odd_size(size)
    image_f64 = ensure_gray_float64(image)
    return cv2.GaussianBlur(image_f64, (size, size), sigmaX=sigma, sigmaY=sigma, borderType=border_type)


def gaussian_kernel_for_crosscheck(size: int, sigma: float = 0.0) -> np.ndarray:
    """Expose the explicit Gaussian kernel used to match ``cv2.GaussianBlur``."""
    return gaussian_kernel(size, sigma)
