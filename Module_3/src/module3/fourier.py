"""Fourier-domain filtering that matches zero-padded linear convolution."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from module3.io_utils import ensure_gray_float64
from module3.spatial import validate_kernel


@dataclass(frozen=True)
class FourierFilterResult:
    """Detailed output from the Fourier filtering path."""

    image: np.ndarray
    padded_image_shape: tuple[int, int]
    max_imaginary_abs: float


def aligned_kernel_fft_array(kernel: np.ndarray, padded_shape: tuple[int, int]) -> np.ndarray:
    """Embed and origin-align a kernel before FFT.

    Args:
        kernel: Odd-sized 2D kernel.
        padded_shape: Target padded image shape.

    Returns:
        A zero-padded kernel array with the kernel center rolled to index ``(0, 0)``.

    Raises:
        ValueError: if the padded shape cannot contain the kernel.
    """
    kernel_f64 = validate_kernel(kernel)
    if padded_shape[0] < kernel_f64.shape[0] or padded_shape[1] < kernel_f64.shape[1]:
        raise ValueError("padded shape must be at least as large as the kernel")
    kh = kernel_f64.shape[0] // 2
    kw = kernel_f64.shape[1] // 2
    padded = np.zeros(padded_shape, dtype=np.float64)
    padded[: kernel_f64.shape[0], : kernel_f64.shape[1]] = kernel_f64
    return np.roll(padded, shift=(-kh, -kw), axis=(0, 1))


def fourier_filter_gray(image: np.ndarray, kernel: np.ndarray) -> FourierFilterResult:
    """Filter a grayscale image by FFT multiplication and inverse FFT.

    The image is zero-padded by the kernel radius on all sides. The kernel is embedded in the
    same padded shape and rolled so its center is the Fourier-domain origin. Cropping
    ``[kh:kh+M, kw:kw+N]`` then returns the same linear convolution region as
    ``cv2.filter2D(..., borderType=cv2.BORDER_CONSTANT)`` for symmetric kernels.

    Args:
        image: Single-channel image.
        kernel: Odd-sized blur kernel.

    Returns:
        A :class:`FourierFilterResult` containing the filtered ``float64`` image.
    """
    image_f64 = ensure_gray_float64(image)
    kernel_f64 = validate_kernel(kernel)
    kh = kernel_f64.shape[0] // 2
    kw = kernel_f64.shape[1] // 2
    height, width = image_f64.shape

    padded_shape = (height + 2 * kh, width + 2 * kw)
    padded_image = np.zeros(padded_shape, dtype=np.float64)
    padded_image[kh : kh + height, kw : kw + width] = image_f64
    padded_kernel = aligned_kernel_fft_array(kernel_f64, padded_shape)

    product = np.fft.fft2(padded_image) * np.fft.fft2(padded_kernel)
    inverse = np.fft.ifft2(product)
    max_imaginary_abs = float(np.max(np.abs(inverse.imag)))
    filtered = inverse.real[kh : kh + height, kw : kw + width]
    return FourierFilterResult(filtered, padded_shape, max_imaginary_abs)


def wrong_unaligned_fourier_filter_gray(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Deliberately wrong FFT path used only by tests to prove alignment matters."""
    image_f64 = ensure_gray_float64(image)
    kernel_f64 = validate_kernel(kernel)
    kh = kernel_f64.shape[0] // 2
    kw = kernel_f64.shape[1] // 2
    height, width = image_f64.shape
    padded_shape = (height + 2 * kh, width + 2 * kw)
    padded_image = np.zeros(padded_shape, dtype=np.float64)
    padded_image[kh : kh + height, kw : kw + width] = image_f64
    padded_kernel = np.zeros(padded_shape, dtype=np.float64)
    padded_kernel[: kernel_f64.shape[0], : kernel_f64.shape[1]] = kernel_f64
    inverse = np.fft.ifft2(np.fft.fft2(padded_image) * np.fft.fft2(padded_kernel))
    return inverse.real[kh : kh + height, kw : kw + width]
