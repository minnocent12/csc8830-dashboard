"""Non-UI diagnostics for calibration and stereo geometry.

These functions return new arrays or write explicitly requested derived files. They do not
mutate original images and do not display results through Streamlit; that belongs to a later
phase.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from module7.io_utils import validate_image_array


def draw_correspondences(
    image1_bgr: np.ndarray,
    image2_bgr: np.ndarray,
    points1: np.ndarray,
    points2: np.ndarray,
    *,
    max_points: int | None = None,
) -> np.ndarray:
    """Create a side-by-side BGR correspondence diagnostic without mutating inputs."""
    first = validate_image_array(image1_bgr, name="image1_bgr", require_color=True)
    second = validate_image_array(image2_bgr, name="image2_bgr", require_color=True)
    p1 = np.asarray(points1, dtype=np.float64).reshape(-1, 2)
    p2 = np.asarray(points2, dtype=np.float64).reshape(-1, 2)
    if p1.shape != p2.shape or not np.isfinite(p1).all() or not np.isfinite(p2).all():
        raise ValueError("points1 and points2 must be matching finite arrays")
    count = p1.shape[0] if max_points is None else min(p1.shape[0], int(max_points))
    if count < 0:
        raise ValueError("max_points must be non-negative")
    height = max(first.shape[0], second.shape[0])
    canvas = np.zeros((height, first.shape[1] + second.shape[1], 3), dtype=first.dtype)
    canvas[: first.shape[0], : first.shape[1]] = first
    canvas[: second.shape[0], first.shape[1] :] = second
    rng = np.random.default_rng(7)
    colors = rng.integers(50, 256, size=(count, 3), dtype=np.uint8)
    for index in range(count):
        color = tuple(int(channel) for channel in colors[index])
        left = tuple(int(round(value)) for value in p1[index])
        right = (int(round(p2[index, 0] + first.shape[1])), int(round(p2[index, 1])))
        cv2.circle(canvas, left, 4, color, -1)
        cv2.circle(canvas, right, 4, color, -1)
        cv2.line(canvas, left, right, color, 1, cv2.LINE_AA)
    return canvas


def draw_reprojection_overlay(
    image_bgr: np.ndarray,
    observed_points: np.ndarray,
    projected_points: np.ndarray,
    *,
    observed_color: tuple[int, int, int] = (0, 255, 0),
    projected_color: tuple[int, int, int] = (0, 0, 255),
) -> np.ndarray:
    """Draw observed/projected points on a copy of a BGR image."""
    image = validate_image_array(image_bgr, name="image_bgr", require_color=True)
    observed = np.asarray(observed_points, dtype=np.float64).reshape(-1, 2)
    projected = np.asarray(projected_points, dtype=np.float64).reshape(-1, 2)
    if observed.shape != projected.shape or not np.isfinite(observed).all() or not np.isfinite(projected).all():
        raise ValueError("observed_points and projected_points must be matching finite arrays")
    output = image.copy()
    for actual, predicted in zip(observed, projected, strict=True):
        actual_xy = tuple(int(round(value)) for value in actual)
        predicted_xy = tuple(int(round(value)) for value in predicted)
        cv2.circle(output, actual_xy, 4, observed_color, 1)
        cv2.drawMarker(output, predicted_xy, projected_color, cv2.MARKER_CROSS, 9, 1)
        cv2.line(output, actual_xy, predicted_xy, (255, 255, 0), 1, cv2.LINE_AA)
    return output


def save_image(image_bgr: np.ndarray, path: str | Path) -> Path:
    """Save a derived BGR diagnostic image to an explicit output path."""
    image = validate_image_array(image_bgr, name="image_bgr", require_color=True)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image):
        raise OSError(f"could not write diagnostic image: {output_path}")
    return output_path
