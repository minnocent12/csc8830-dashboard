"""File and image utilities for the Module 7 core pipeline.

OpenCV decodes color images in BGR order. These helpers preserve that convention and never
mutate source arrays or source files. The functions deliberately do not create synthetic
images or calibration records when an input is absent.
"""
from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

import cv2
import numpy as np

SUPPORTED_IMAGE_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"})


def validate_image_array(
    image: np.ndarray,
    *,
    name: str = "image",
    require_color: bool | None = None,
) -> np.ndarray:
    """Validate a non-empty image array and return it unchanged.

    Color images are expected to be BGR when passed to OpenCV functions. Grayscale images are
    two-dimensional. Floating-point arrays must contain only finite values.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"{name} must be a numpy.ndarray")
    if image.ndim not in (2, 3):
        raise ValueError(f"{name} must be 2D grayscale or 3D color, got {image.ndim}D")
    if image.shape[0] <= 0 or image.shape[1] <= 0:
        raise ValueError(f"{name} must have positive height and width")
    if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
        raise ValueError(f"{name} must have 1, 3, or 4 channels, got {image.shape[2]}")
    if image.dtype.kind in "fc" and not np.isfinite(image).all():
        raise ValueError(f"{name} contains non-finite values")
    if require_color is True and (image.ndim != 3 or image.shape[2] != 3):
        raise ValueError(f"{name} must be a 3-channel BGR image")
    if require_color is False and image.ndim == 3 and image.shape[2] != 1:
        raise ValueError(f"{name} must be a grayscale image")
    return image


def load_image_bgr(path: str | Path) -> np.ndarray:
    """Load a color image as a copied BGR array without modifying the file."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"unsupported image suffix: {image_path.suffix}")
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"could not decode color image: {image_path}")
    return validate_image_array(image, name="loaded BGR image", require_color=True).copy()


def load_images_bgr(paths: list[str | Path]) -> list[np.ndarray]:
    """Load multiple BGR images and require one shared image size."""
    if not paths:
        raise ValueError("at least one image path is required")
    images = [load_image_bgr(path) for path in paths]
    ensure_same_image_size(images)
    return images


def read_correspondence_csv(path: str | Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Read the shared ``point_id,u1,v1,u2,v2`` correspondence format.

    Coordinates remain raw pixel values; calibration-aware callers perform undistortion through
    the existing stereo-geometry API.  IDs are required to be non-empty and unique so that a
    shape measurement can refer to landmarks without positional ambiguity.
    """
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    required = {"point_id", "u1", "v1", "u2", "v2"}
    point_ids: list[str] = []
    first: list[list[float]] = []
    second: list[list[float]] = []
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"correspondence CSV must contain columns: {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            identifier = str(row["point_id"]).strip()
            try:
                coordinates1 = [float(row["u1"]), float(row["v1"])]
                coordinates2 = [float(row["u2"]), float(row["v2"])]
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid correspondence at CSV row {row_number}") from exc
            if not identifier or not np.isfinite(coordinates1 + coordinates2).all():
                raise ValueError(f"invalid correspondence at CSV row {row_number}")
            if identifier in point_ids:
                raise ValueError(f"duplicate point_id at CSV row {row_number}: {identifier}")
            point_ids.append(identifier)
            first.append(coordinates1)
            second.append(coordinates2)
    if not point_ids:
        raise ValueError("correspondence CSV contains no rows")
    return point_ids, np.asarray(first, dtype=np.float64), np.asarray(second, dtype=np.float64)


def ensure_same_image_size(images: list[np.ndarray] | tuple[np.ndarray, ...]) -> tuple[int, int]:
    """Return ``(width, height)`` after requiring all images to share a size."""
    if not images:
        raise ValueError("at least one image is required")
    sizes = {(int(image.shape[1]), int(image.shape[0])) for image in images}
    if len(sizes) != 1:
        raise ValueError(f"all images must share one size, got {sorted(sizes)}")
    return next(iter(sizes))


def _json_default(value: Any) -> Any:
    """Convert common NumPy scalar/array values to JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write a JSON record to a new/explicit output path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n", encoding="utf-8")
    return output_path


def read_json(path: str | Path) -> dict[str, Any]:
    """Read a JSON object from disk and reject non-object payloads."""
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {input_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {input_path}")
    return payload
