"""Image input/output helpers with explicit OpenCV color-space conventions."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ImageArray = np.ndarray


def load_image_bgr(path: str | Path) -> ImageArray:
    """Load an image with OpenCV in BGR channel order.

    Args:
        path: Image file path.

    Returns:
        A ``uint8`` BGR image with shape ``(height, width, 3)``.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if OpenCV cannot decode the image as a color image.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"could not decode color image: {image_path}")
    return image


def decode_image_bgr(data: bytes) -> ImageArray:
    """Decode uploaded image bytes as a BGR ``uint8`` image.

    Args:
        data: Encoded image bytes from a file upload.

    Returns:
        A ``uint8`` BGR image.

    Raises:
        ValueError: if the bytes cannot be decoded as a color image.
    """
    raw = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("could not decode uploaded image")
    return image


def bgr_to_gray_float64(image_bgr: ImageArray) -> ImageArray:
    """Convert a BGR ``uint8`` image to grayscale ``float64`` in the 0-255 range.

    Args:
        image_bgr: BGR image with shape ``(height, width, 3)``.

    Returns:
        A single-channel ``float64`` image.

    Raises:
        ValueError: if the input is not a color image.
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("expected a BGR image with shape (height, width, 3)")
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return gray.astype(np.float64, copy=False)


def ensure_gray_float64(image: ImageArray) -> ImageArray:
    """Validate and convert a 2D image to grayscale ``float64``.

    Args:
        image: A single-channel image.

    Returns:
        A copy-free ``float64`` view when possible.

    Raises:
        ValueError: if ``image`` is not a finite 2D array.
    """
    array = np.asarray(image)
    if array.ndim != 2:
        raise ValueError("expected a single-channel 2D image")
    result = array.astype(np.float64, copy=False)
    if not np.all(np.isfinite(result)):
        raise ValueError("image contains non-finite values")
    return result


def to_display_uint8(image: ImageArray) -> ImageArray:
    """Clip and round an image to ``uint8`` for display or saving.

    Args:
        image: Numeric image in nominal 0-255 range.

    Returns:
        A clipped ``uint8`` image. This helper is intentionally not used before metrics.
    """
    return np.clip(np.rint(np.asarray(image)), 0, 255).astype(np.uint8)


def save_image(path: str | Path, image: ImageArray) -> None:
    """Save an image with OpenCV, creating parent directories as needed.

    Args:
        path: Output path.
        image: Image array in OpenCV-compatible channel order.

    Raises:
        ValueError: if OpenCV fails to write the file.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(output_path), image)
    if not ok:
        raise ValueError(f"could not write image: {output_path}")
