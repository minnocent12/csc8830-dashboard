"""Single-camera checkerboard calibration for Module 7.

The calibration workflow estimates the phone's intrinsic matrix and lens distortion from
user-supplied images. It never invents camera parameters. The resulting record is reusable by
the sequential-stereo geometry functions and preserves the target size, image size, source
image identifiers, flags, and reprojection errors needed for academic provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

from module7.io_utils import load_image_bgr, read_json, write_json

SUPPORTED_SQUARE_UNITS = frozenset({"m", "mm"})
_SUBPIXEL_CRITERIA = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    40,
    1e-3,
)


def _as_float_matrix(value: object, *, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains non-finite values")
    return array


def validate_pattern_size(pattern_size: tuple[int, int]) -> tuple[int, int]:
    """Validate checkerboard inner-corner dimensions as ``(columns, rows)``."""
    if len(pattern_size) != 2:
        raise ValueError("pattern_size must contain (columns, rows)")
    columns, rows = (int(pattern_size[0]), int(pattern_size[1]))
    if columns < 2 or rows < 2:
        raise ValueError("checkerboard pattern_size dimensions must each be at least 2")
    return columns, rows


def validate_square_size(square_size: float, square_unit: str) -> tuple[float, str]:
    """Validate a positive physical checkerboard square size and unit."""
    size = float(square_size)
    if not np.isfinite(size) or size <= 0:
        raise ValueError("square_size must be a finite positive value")
    unit = str(square_unit).strip()
    if unit not in SUPPORTED_SQUARE_UNITS:
        raise ValueError(f"square_unit must be one of {sorted(SUPPORTED_SQUARE_UNITS)}")
    return size, unit


def checkerboard_object_points(
    pattern_size: tuple[int, int],
    square_size: float,
    *,
    square_unit: str = "mm",
) -> np.ndarray:
    """Create metric checkerboard points on the plane ``Z=0``.

    The returned array has shape ``(columns*rows, 3)`` and follows OpenCV's row-major
    checkerboard corner order. Coordinates use the supplied physical square unit.
    """
    columns, rows = validate_pattern_size(pattern_size)
    size, _ = validate_square_size(square_size, square_unit)
    grid = np.zeros((columns * rows, 3), dtype=np.float64)
    grid[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2) * size
    return grid


def _image_to_gray(image: np.ndarray) -> np.ndarray:
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a numpy.ndarray")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("image must be grayscale or a 3-channel BGR array")
    if gray.size == 0:
        raise ValueError("image must not be empty")
    return gray


def detect_checkerboard_corners(
    image: np.ndarray,
    pattern_size: tuple[int, int],
    *,
    refine: bool = True,
) -> np.ndarray | None:
    """Detect checkerboard inner corners in a BGR or grayscale image.

    ``None`` means the pattern was not detected; it is not replaced with synthetic points.
    ``findChessboardCornersSB`` is preferred when available, with the classic detector as a
    compatibility fallback. Corner refinement never mutates the source image.
    """
    pattern = validate_pattern_size(pattern_size)
    gray = _image_to_gray(image)
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, pattern, flags=cv2.CALIB_CB_EXHAUSTIVE)
    else:
        found, corners = cv2.findChessboardCorners(
            gray,
            pattern,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
    if not found or corners is None:
        return None
    corners = np.asarray(corners, dtype=np.float32).reshape(-1, 1, 2)
    if refine and not hasattr(cv2, "findChessboardCornersSB"):
        corners = cv2.cornerSubPix(
            gray,
            corners,
            winSize=(11, 11),
            zeroZone=(-1, -1),
            criteria=_SUBPIXEL_CRITERIA,
        )
    return corners.astype(np.float64)


def _validate_calibration_points(
    object_points: Sequence[np.ndarray],
    image_points: Sequence[np.ndarray],
    image_size: tuple[int, int],
) -> tuple[list[np.ndarray], list[np.ndarray], tuple[int, int]]:
    if len(object_points) != len(image_points):
        raise ValueError("object_points and image_points must have the same number of views")
    if len(object_points) < 3:
        raise ValueError("at least three calibration views are required")
    width, height = (int(image_size[0]), int(image_size[1]))
    if width <= 0 or height <= 0:
        raise ValueError("image_size must contain positive (width, height)")
    objects: list[np.ndarray] = []
    images: list[np.ndarray] = []
    expected_count: int | None = None
    for index, (obj, img) in enumerate(zip(object_points, image_points, strict=True)):
        obj_array = np.asarray(obj, dtype=np.float64).reshape(-1, 3)
        img_array = np.asarray(img, dtype=np.float64).reshape(-1, 2)
        if obj_array.shape[0] != img_array.shape[0]:
            raise ValueError(f"view {index} has mismatched object/image point counts")
        if obj_array.shape[0] < 4:
            raise ValueError(f"view {index} must contain at least four calibration points")
        if expected_count is None:
            expected_count = obj_array.shape[0]
        if obj_array.shape[0] != expected_count:
            raise ValueError("all calibration views must contain the same number of points")
        if not np.isfinite(obj_array).all() or not np.isfinite(img_array).all():
            raise ValueError(f"view {index} contains non-finite calibration points")
        objects.append(obj_array)
        images.append(img_array)
    return objects, images, (width, height)


def _per_view_reprojection_error(
    object_points: Sequence[np.ndarray],
    image_points: Sequence[np.ndarray],
    rvecs: Sequence[np.ndarray],
    tvecs: Sequence[np.ndarray],
    camera_matrix: np.ndarray,
    distortion: np.ndarray,
) -> list[float]:
    errors: list[float] = []
    for obj, observed, rvec, tvec in zip(object_points, image_points, rvecs, tvecs, strict=True):
        projected, _ = cv2.projectPoints(obj, rvec, tvec, camera_matrix, distortion)
        predicted = projected.reshape(-1, 2)
        residuals = np.linalg.norm(predicted - observed, axis=1)
        errors.append(float(np.sqrt(np.mean(residuals**2))))
    return errors


@dataclass(frozen=True)
class CalibrationResult:
    """Serializable result of one real or synthetic camera-calibration run."""

    calibration_id: str
    image_size: tuple[int, int]
    pattern_size: tuple[int, int]
    square_size: float
    square_unit: str
    camera_matrix: np.ndarray
    distortion_coefficients: np.ndarray
    rms_reprojection_error_px: float
    per_view_reprojection_error_px: tuple[float, ...]
    rotation_vectors: tuple[np.ndarray, ...] = field(default_factory=tuple)
    translation_vectors: tuple[np.ndarray, ...] = field(default_factory=tuple)
    source_image_ids: tuple[str, ...] = field(default_factory=tuple)
    flags: int = 0
    status: str = "tested"

    def __post_init__(self) -> None:
        if not str(self.calibration_id).strip():
            raise ValueError("calibration_id must not be empty")
        width, height = self.image_size
        if int(width) <= 0 or int(height) <= 0:
            raise ValueError("image_size must contain positive values")
        object.__setattr__(self, "image_size", (int(width), int(height)))
        object.__setattr__(self, "pattern_size", validate_pattern_size(self.pattern_size))
        size, unit = validate_square_size(self.square_size, self.square_unit)
        object.__setattr__(self, "square_size", size)
        object.__setattr__(self, "square_unit", unit)
        K = _as_float_matrix(self.camera_matrix, shape=(3, 3), name="camera_matrix")
        if np.linalg.det(K) == 0 or K[0, 0] <= 0 or K[1, 1] <= 0 or K[2, 2] <= 0:
            raise ValueError("camera_matrix must be non-singular with positive focal lengths and K[2,2]")
        D = np.asarray(self.distortion_coefficients, dtype=np.float64).reshape(-1)
        if D.size == 0 or not np.isfinite(D).all():
            raise ValueError("distortion_coefficients must be a finite non-empty vector")
        object.__setattr__(self, "camera_matrix", K)
        object.__setattr__(self, "distortion_coefficients", D)
        rms = float(self.rms_reprojection_error_px)
        if not np.isfinite(rms) or rms < 0:
            raise ValueError("rms_reprojection_error_px must be finite and non-negative")
        object.__setattr__(self, "rms_reprojection_error_px", rms)
        per_view = tuple(float(value) for value in self.per_view_reprojection_error_px)
        if any(not np.isfinite(value) or value < 0 for value in per_view):
            raise ValueError("per-view reprojection errors must be finite and non-negative")
        object.__setattr__(self, "per_view_reprojection_error_px", per_view)
        object.__setattr__(self, "rotation_vectors", tuple(np.asarray(v, dtype=np.float64) for v in self.rotation_vectors))
        object.__setattr__(self, "translation_vectors", tuple(np.asarray(v, dtype=np.float64) for v in self.translation_vectors))
        if self.source_image_ids and len(self.source_image_ids) != len(per_view):
            raise ValueError("source_image_ids must match the number of per-view errors")

    @property
    def focal_length_px(self) -> tuple[float, float]:
        """Return calibrated ``(fx, fy)`` in pixels."""
        return float(self.camera_matrix[0, 0]), float(self.camera_matrix[1, 1])

    def to_dict(self) -> dict[str, object]:
        """Convert the result to a JSON-compatible dictionary."""
        return {
            "schema_version": 1,
            "calibration_id": self.calibration_id,
            "image_size": list(self.image_size),
            "pattern_size": list(self.pattern_size),
            "square_size": self.square_size,
            "square_unit": self.square_unit,
            "camera_matrix": self.camera_matrix.tolist(),
            "distortion_coefficients": self.distortion_coefficients.tolist(),
            "rms_reprojection_error_px": self.rms_reprojection_error_px,
            "per_view_reprojection_error_px": list(self.per_view_reprojection_error_px),
            "rotation_vectors": [vector.tolist() for vector in self.rotation_vectors],
            "translation_vectors": [vector.tolist() for vector in self.translation_vectors],
            "source_image_ids": list(self.source_image_ids),
            "flags": int(self.flags),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "CalibrationResult":
        """Construct and validate a calibration result from JSON data."""
        required = {
            "calibration_id",
            "image_size",
            "pattern_size",
            "square_size",
            "square_unit",
            "camera_matrix",
            "distortion_coefficients",
            "rms_reprojection_error_px",
            "per_view_reprojection_error_px",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"calibration record is missing fields: {', '.join(missing)}")
        return cls(
            calibration_id=str(payload["calibration_id"]),
            image_size=tuple(payload["image_size"]),  # type: ignore[arg-type]
            pattern_size=tuple(payload["pattern_size"]),  # type: ignore[arg-type]
            square_size=float(payload["square_size"]),
            square_unit=str(payload["square_unit"]),
            camera_matrix=np.asarray(payload["camera_matrix"], dtype=np.float64),
            distortion_coefficients=np.asarray(payload["distortion_coefficients"], dtype=np.float64),
            rms_reprojection_error_px=float(payload["rms_reprojection_error_px"]),
            per_view_reprojection_error_px=tuple(payload["per_view_reprojection_error_px"]),  # type: ignore[arg-type]
            rotation_vectors=tuple(np.asarray(v, dtype=np.float64) for v in payload.get("rotation_vectors", [])),  # type: ignore[arg-type]
            translation_vectors=tuple(np.asarray(v, dtype=np.float64) for v in payload.get("translation_vectors", [])),  # type: ignore[arg-type]
            source_image_ids=tuple(str(value) for value in payload.get("source_image_ids", [])),  # type: ignore[arg-type]
            flags=int(payload.get("flags", 0)),
            status=str(payload.get("status", "tested")),
        )


def calibrate_camera_from_points(
    object_points: Sequence[np.ndarray],
    image_points: Sequence[np.ndarray],
    image_size: tuple[int, int],
    *,
    pattern_size: tuple[int, int],
    square_size: float,
    square_unit: str = "mm",
    calibration_id: str = "calibration",
    source_image_ids: Sequence[str] | None = None,
    flags: int = 0,
) -> CalibrationResult:
    """Calibrate a camera from corresponding metric object/image point sets.

    This function is the deterministic core used by image-based calibration and synthetic
    tests. It accepts only observed/provided points; it never creates calibration observations.
    """
    objects, images, size = _validate_calibration_points(object_points, image_points, image_size)
    pattern = validate_pattern_size(pattern_size)
    square, unit = validate_square_size(square_size, square_unit)
    expected_points = pattern[0] * pattern[1]
    if objects[0].shape[0] != expected_points:
        raise ValueError(
            f"point count {objects[0].shape[0]} does not match pattern_size product {expected_points}"
        )
    if source_image_ids is not None and len(source_image_ids) != len(objects):
        raise ValueError("source_image_ids must match the number of calibration views")
    try:
        rms, camera_matrix, distortion, rvecs, tvecs = cv2.calibrateCamera(
            [points.astype(np.float32) for points in objects],
            [points.astype(np.float32) for points in images],
            size,
            None,
            None,
            flags=int(flags),
        )
    except cv2.error as exc:
        raise ValueError(f"OpenCV camera calibration failed: {exc}") from exc
    per_view = _per_view_reprojection_error(
        objects,
        images,
        rvecs,
        tvecs,
        camera_matrix,
        distortion,
    )
    return CalibrationResult(
        calibration_id=calibration_id,
        image_size=size,
        pattern_size=pattern,
        square_size=square,
        square_unit=unit,
        camera_matrix=camera_matrix,
        distortion_coefficients=distortion,
        rms_reprojection_error_px=float(rms),
        per_view_reprojection_error_px=tuple(per_view),
        rotation_vectors=tuple(np.asarray(vector) for vector in rvecs),
        translation_vectors=tuple(np.asarray(vector) for vector in tvecs),
        source_image_ids=tuple(source_image_ids or ()),
        flags=int(flags),
        status="tested",
    )


def calibrate_camera_from_image_paths(
    image_paths: Sequence[str | Path],
    *,
    pattern_size: tuple[int, int],
    square_size: float,
    square_unit: str = "mm",
    calibration_id: str = "calibration",
    refine: bool = True,
    flags: int = 0,
) -> CalibrationResult:
    """Detect a checkerboard in real image paths and calibrate from accepted views."""
    if not image_paths:
        raise ValueError("at least one calibration image path is required")
    images = [load_image_bgr(path) for path in image_paths]
    sizes = {(int(image.shape[1]), int(image.shape[0])) for image in images}
    if len(sizes) != 1:
        raise ValueError(f"calibration images must share one size, got {sorted(sizes)}")
    object_template = checkerboard_object_points(pattern_size, square_size, square_unit=square_unit)
    accepted_objects: list[np.ndarray] = []
    accepted_images: list[np.ndarray] = []
    accepted_ids: list[str] = []
    rejected: list[str] = []
    for path, image in zip(image_paths, images, strict=True):
        corners = detect_checkerboard_corners(image, pattern_size, refine=refine)
        if corners is None:
            rejected.append(str(path))
            continue
        accepted_objects.append(object_template.copy())
        accepted_images.append(corners.reshape(-1, 2))
        accepted_ids.append(str(path))
    if len(accepted_images) < 3:
        raise ValueError(
            f"only {len(accepted_images)} calibration views contained the checkerboard; "
            f"at least three are required. Rejected: {rejected}"
        )
    result = calibrate_camera_from_points(
        accepted_objects,
        accepted_images,
        (images[0].shape[1], images[0].shape[0]),
        pattern_size=pattern_size,
        square_size=square_size,
        square_unit=square_unit,
        calibration_id=calibration_id,
        source_image_ids=accepted_ids,
        flags=flags,
    )
    return result


def save_calibration(result: CalibrationResult, path: str | Path) -> Path:
    """Persist a validated calibration record as JSON."""
    if not isinstance(result, CalibrationResult):
        raise TypeError("result must be a CalibrationResult")
    return write_json(path, result.to_dict())


def load_calibration(path: str | Path) -> CalibrationResult:
    """Load and validate a persisted calibration record."""
    return CalibrationResult.from_dict(read_json(path))
