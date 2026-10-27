"""Sequential calibrated-stereo geometry for one moving smartphone.

The primary pose path estimates a relative rotation and translation direction from calibrated
image correspondences. The essential matrix does not provide metric translation magnitude, so
the caller must supply a physically valid baseline or use the checkerboard-pose fallback. The
functions below make that distinction explicit and flag invalid geometry instead of silently
reporting depth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import cv2
import numpy as np


class StereoGeometryError(ValueError):
    """Raised when sequential-stereo geometry cannot support a valid reconstruction."""


def validate_camera_matrix(camera_matrix: np.ndarray) -> np.ndarray:
    """Validate and copy a finite, non-singular 3x3 intrinsic matrix."""
    matrix = np.asarray(camera_matrix, dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError(f"camera_matrix must have shape (3, 3), got {matrix.shape}")
    if not np.isfinite(matrix).all() or np.linalg.det(matrix) == 0:
        raise ValueError("camera_matrix must be finite and non-singular")
    if matrix[0, 0] <= 0 or matrix[1, 1] <= 0 or matrix[2, 2] <= 0:
        raise ValueError("camera_matrix focal lengths and homogeneous scale must be positive")
    return matrix.copy()


def validate_distortion_coefficients(distortion_coefficients: np.ndarray | None) -> np.ndarray:
    """Return a finite distortion vector, using zero distortion only when explicitly omitted."""
    if distortion_coefficients is None:
        return np.zeros(5, dtype=np.float64)
    distortion = np.asarray(distortion_coefficients, dtype=np.float64).reshape(-1)
    if distortion.size == 0 or not np.isfinite(distortion).all():
        raise ValueError("distortion_coefficients must be a finite non-empty vector")
    return distortion.copy()


def _validate_points(points: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one point")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains non-finite values")
    return array


def validate_correspondences(
    points1: np.ndarray,
    points2: np.ndarray,
    *,
    minimum_count: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate paired 2D points for a two-view operation."""
    first = _validate_points(points1, name="points1")
    second = _validate_points(points2, name="points2")
    if first.shape != second.shape:
        raise ValueError(f"points1 and points2 must have the same shape, got {first.shape} and {second.shape}")
    if first.shape[0] < int(minimum_count):
        raise ValueError(f"at least {minimum_count} correspondences are required")
    return first, second


def undistort_points_to_pixel(
    points: np.ndarray,
    camera_matrix: np.ndarray,
    distortion_coefficients: np.ndarray | None = None,
) -> np.ndarray:
    """Undistort raw pixel points while retaining pixel units via ``P=K``."""
    point_array = _validate_points(points, name="points")
    K = validate_camera_matrix(camera_matrix)
    distortion = validate_distortion_coefficients(distortion_coefficients)
    corrected = cv2.undistortPoints(point_array.reshape(-1, 1, 2), K, distortion, P=K)
    corrected = corrected.reshape(-1, 2)
    if not np.isfinite(corrected).all():
        raise StereoGeometryError("undistortion produced non-finite image points")
    return corrected


def apply_metric_scale(translation_direction: np.ndarray, baseline: float) -> np.ndarray:
    """Scale a translation direction by a positive camera-center displacement.

    The supplied baseline must be measured in a declared physical unit. This function performs
    only the numerical scale application; it cannot determine whether the measurement was made
    between optical centers, so that provenance is stored by the caller.
    """
    direction = np.asarray(translation_direction, dtype=np.float64).reshape(-1)
    if direction.shape != (3,) or not np.isfinite(direction).all():
        raise ValueError("translation_direction must be a finite length-3 vector")
    norm = float(np.linalg.norm(direction))
    if norm <= 0:
        raise ValueError("translation_direction must have non-zero norm")
    scale = float(baseline)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("baseline must be a finite positive value")
    return direction / norm * scale


def _validate_rotation(rotation: np.ndarray) -> np.ndarray:
    matrix = np.asarray(rotation, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("rotation must be a finite 3x3 matrix")
    if not np.allclose(matrix.T @ matrix, np.eye(3), atol=1e-5) or np.linalg.det(matrix) <= 0:
        raise ValueError("rotation must be a proper orthonormal rotation matrix")
    return matrix.copy()


@dataclass(frozen=True)
class StereoPose:
    """Relative pose satisfying ``X2 = R @ X1 + t``.

    ``translation_unit`` is the direction recovered from essential geometry. ``translation_metric``
    is present only when a measured baseline or metric checkerboard pose supplied scale.
    """

    rotation: np.ndarray
    translation_unit: np.ndarray
    translation_metric: np.ndarray | None
    essential_matrix: np.ndarray | None
    inlier_mask: np.ndarray
    baseline: float | None
    baseline_unit: str | None
    scale_source: str | None
    method: str
    median_parallax_degrees: float
    baseline_uncertainty: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rotation", _validate_rotation(self.rotation))
        unit = np.asarray(self.translation_unit, dtype=np.float64).reshape(-1)
        if unit.shape != (3,) or not np.isfinite(unit).all() or np.linalg.norm(unit) <= 0:
            raise ValueError("translation_unit must be a finite non-zero length-3 vector")
        object.__setattr__(self, "translation_unit", unit / np.linalg.norm(unit))
        if self.translation_metric is not None:
            metric = np.asarray(self.translation_metric, dtype=np.float64).reshape(-1)
            if metric.shape != (3,) or not np.isfinite(metric).all() or np.linalg.norm(metric) <= 0:
                raise ValueError("translation_metric must be a finite non-zero length-3 vector")
            object.__setattr__(self, "translation_metric", metric)
        if self.essential_matrix is not None:
            essential = np.asarray(self.essential_matrix, dtype=np.float64)
            if essential.shape != (3, 3) or not np.isfinite(essential).all():
                raise ValueError("essential_matrix must be a finite 3x3 matrix")
            object.__setattr__(self, "essential_matrix", essential)
        mask = np.asarray(self.inlier_mask, dtype=bool).reshape(-1)
        if mask.size == 0:
            raise ValueError("inlier_mask must not be empty")
        object.__setattr__(self, "inlier_mask", mask)
        if self.baseline is not None:
            baseline = float(self.baseline)
            if not np.isfinite(baseline) or baseline <= 0:
                raise ValueError("baseline must be finite and positive")
            if self.baseline_unit not in {"m", "mm"}:
                raise ValueError("baseline_unit must be 'm' or 'mm' when baseline is supplied")
            object.__setattr__(self, "baseline", baseline)
        if not np.isfinite(float(self.median_parallax_degrees)) or self.median_parallax_degrees < 0:
            raise ValueError("median_parallax_degrees must be finite and non-negative")
        if self.baseline_uncertainty is not None:
            uncertainty = float(self.baseline_uncertainty)
            if self.baseline is None:
                raise ValueError("baseline_uncertainty requires a metric baseline")
            if not np.isfinite(uncertainty) or uncertainty < 0:
                raise ValueError("baseline_uncertainty must be finite and non-negative")
            object.__setattr__(self, "baseline_uncertainty", uncertainty)

    @property
    def is_metric(self) -> bool:
        """Whether translation scale is attached to a physical unit."""
        return self.translation_metric is not None and self.baseline is not None

    @property
    def relative_scale_uncertainty(self) -> float | None:
        """Return baseline uncertainty divided by baseline when supplied."""
        if self.baseline is None or self.baseline_uncertainty is None:
            return None
        return float(self.baseline_uncertainty / self.baseline)

    def projection_matrices(
        self,
        camera_matrix: np.ndarray,
        *,
        require_metric: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Build ``P1`` and ``P2`` for the selected camera coordinate frame."""
        K = validate_camera_matrix(camera_matrix)
        if require_metric and not self.is_metric:
            raise StereoGeometryError("metric projection requested but no physical translation scale is attached")
        translation = self.translation_metric if self.translation_metric is not None else self.translation_unit
        P1 = K @ np.hstack((np.eye(3), np.zeros((3, 1))))
        P2 = K @ np.hstack((self.rotation, translation.reshape(3, 1)))
        return P1, P2


@dataclass(frozen=True)
class CheckerboardPose:
    """Metric pose of a calibration board: ``X_camera = R @ X_board + t``."""

    rotation: np.ndarray
    translation: np.ndarray
    reprojection_error_px: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "rotation", _validate_rotation(self.rotation))
        translation = np.asarray(self.translation, dtype=np.float64).reshape(-1)
        if translation.shape != (3,) or not np.isfinite(translation).all():
            raise ValueError("translation must be a finite length-3 vector")
        object.__setattr__(self, "translation", translation)
        error = float(self.reprojection_error_px)
        if not np.isfinite(error) or error < 0:
            raise ValueError("reprojection_error_px must be finite and non-negative")


@dataclass(frozen=True)
class RectificationResult:
    """Outputs of OpenCV stereo rectification for one sequential pair."""

    R1: np.ndarray
    R2: np.ndarray
    P1: np.ndarray
    P2: np.ndarray
    Q: np.ndarray
    valid_roi1: tuple[int, int, int, int]
    valid_roi2: tuple[int, int, int, int]


@dataclass(frozen=True)
class TriangulationResult:
    """Sparse 3D points and quality flags in camera 1's coordinate frame."""

    points_3d: np.ndarray
    valid_mask: np.ndarray
    reprojection_error_view1_px: np.ndarray
    reprojection_error_view2_px: np.ndarray
    unit: str | None
    metric: bool
    median_parallax_degrees: float

    @property
    def valid_points(self) -> np.ndarray:
        """Return only points passing finite/positive-depth validation."""
        return self.points_3d[self.valid_mask]


def _parallax_angles_degrees(
    points1_undistorted: np.ndarray,
    points2_undistorted: np.ndarray,
    camera_matrix: np.ndarray,
    rotation: np.ndarray,
) -> np.ndarray:
    K = validate_camera_matrix(camera_matrix)
    R = _validate_rotation(rotation)
    rays1 = (np.linalg.inv(K) @ np.hstack((points1_undistorted, np.ones((len(points1_undistorted), 1)))).T).T
    rays2 = (np.linalg.inv(K) @ np.hstack((points2_undistorted, np.ones((len(points2_undistorted), 1)))).T).T
    rays1 /= np.linalg.norm(rays1, axis=1, keepdims=True)
    rays2_in_1 = (R.T @ rays2.T).T
    rays2_in_1 /= np.linalg.norm(rays2_in_1, axis=1, keepdims=True)
    cosine = np.clip(np.sum(rays1 * rays2_in_1, axis=1), -1.0, 1.0)
    return np.degrees(np.arccos(cosine))


def estimate_relative_pose(
    points1: np.ndarray,
    points2: np.ndarray,
    camera_matrix: np.ndarray,
    *,
    distortion_coefficients: np.ndarray | None = None,
    baseline: float | None = None,
    baseline_unit: str | None = None,
    baseline_uncertainty: float | None = None,
    scale_source: str | None = None,
    method: int = cv2.RANSAC,
    probability: float = 0.999,
    threshold_px: float = 1.0,
    minimum_correspondences: int = 5,
    minimum_parallax_degrees: float = 0.01,
) -> StereoPose:
    """Estimate sequential relative pose and optionally attach measured metric scale.

    Input points are raw image pixels. They are undistorted into pixel coordinates before
    essential-matrix estimation. The returned pose obeys ``X2 = R @ X1 + t``. The translation
    direction is unit length unless ``baseline`` supplies a physical scale.
    """
    first, second = validate_correspondences(points1, points2, minimum_count=minimum_correspondences)
    K = validate_camera_matrix(camera_matrix)
    if not np.isfinite(float(probability)) or not 0 < probability <= 1:
        raise ValueError("probability must be in (0, 1]")
    if not np.isfinite(float(threshold_px)) or threshold_px <= 0:
        raise ValueError("threshold_px must be finite and positive")
    if baseline is not None:
        if baseline_unit not in {"m", "mm"}:
            raise ValueError("baseline_unit must be 'm' or 'mm' when baseline is supplied")
        if scale_source is None or not str(scale_source).strip():
            raise ValueError("scale_source is required when baseline is supplied")
    elif baseline_uncertainty is not None:
        raise ValueError("baseline_uncertainty requires a metric baseline")
    if baseline_uncertainty is not None and (
        not np.isfinite(float(baseline_uncertainty)) or float(baseline_uncertainty) < 0
    ):
        raise ValueError("baseline_uncertainty must be finite and non-negative")
    first_u = undistort_points_to_pixel(first, K, distortion_coefficients)
    second_u = undistort_points_to_pixel(second, K, distortion_coefficients)
    try:
        essential, essential_mask = cv2.findEssentialMat(
            first_u,
            second_u,
            K,
            method=method,
            prob=float(probability),
            threshold=float(threshold_px),
        )
    except cv2.error as exc:
        raise StereoGeometryError(f"essential-matrix estimation failed: {exc}") from exc
    if essential is None:
        raise StereoGeometryError("essential-matrix estimation returned no matrix")
    essential = np.asarray(essential, dtype=np.float64)
    if essential.shape != (3, 3):
        essential = essential[:3, :3]
    if essential.shape != (3, 3) or not np.isfinite(essential).all():
        raise StereoGeometryError(f"essential matrix has invalid shape/value: {essential.shape}")
    initial_mask = np.asarray(essential_mask, dtype=np.uint8).reshape(-1) > 0
    if int(initial_mask.sum()) < minimum_correspondences:
        raise StereoGeometryError("essential-matrix estimation retained too few inliers")
    try:
        recovered_count, rotation, translation, pose_mask = cv2.recoverPose(
            essential,
            first_u,
            second_u,
            K,
            mask=(initial_mask.astype(np.uint8) * 255),
        )
    except cv2.error as exc:
        raise StereoGeometryError(f"relative-pose recovery failed: {exc}") from exc
    inlier_mask = np.asarray(pose_mask, dtype=np.uint8).reshape(-1) > 0
    if int(recovered_count) < minimum_correspondences or int(inlier_mask.sum()) < minimum_correspondences:
        raise StereoGeometryError("pose recovery retained too few inliers")
    rotation = _validate_rotation(rotation)
    translation_direction = np.asarray(translation, dtype=np.float64).reshape(-1)
    if translation_direction.shape != (3,) or np.linalg.norm(translation_direction) <= 0:
        raise StereoGeometryError("pose recovery returned no usable translation direction")
    translation_direction /= np.linalg.norm(translation_direction)
    parallax = _parallax_angles_degrees(first_u[inlier_mask], second_u[inlier_mask], K, rotation)
    median_parallax = float(np.median(parallax))
    if median_parallax < float(minimum_parallax_degrees):
        raise StereoGeometryError(
            f"insufficient triangulation parallax: median {median_parallax:.6g} degrees"
        )
    metric_translation = None
    if baseline is not None:
        metric_translation = apply_metric_scale(translation_direction, baseline)
    return StereoPose(
        rotation=rotation,
        translation_unit=translation_direction,
        translation_metric=metric_translation,
        essential_matrix=essential,
        inlier_mask=inlier_mask,
        baseline=float(baseline) if baseline is not None else None,
        baseline_unit=baseline_unit,
        scale_source=scale_source,
        method="essential_matrix",
        median_parallax_degrees=median_parallax,
        baseline_uncertainty=float(baseline_uncertainty) if baseline_uncertainty is not None else None,
    )


def estimate_checkerboard_pose(
    image_points: np.ndarray,
    object_points: np.ndarray,
    camera_matrix: np.ndarray,
    distortion_coefficients: np.ndarray | None = None,
    *,
    flags: int = cv2.SOLVEPNP_ITERATIVE,
) -> CheckerboardPose:
    """Estimate a metric board-to-camera pose from known checkerboard coordinates."""
    image = _validate_points(image_points, name="image_points")
    objects = np.asarray(object_points, dtype=np.float64).reshape(-1, 3)
    if objects.shape[0] != image.shape[0] or objects.shape[0] < 4:
        raise ValueError("at least four matching checkerboard 3D/2D points are required")
    if not np.isfinite(objects).all():
        raise ValueError("object_points contains non-finite values")
    K = validate_camera_matrix(camera_matrix)
    D = validate_distortion_coefficients(distortion_coefficients)
    try:
        success, rvec, tvec = cv2.solvePnP(objects, image, K, D, flags=flags)
    except cv2.error as exc:
        raise StereoGeometryError(f"checkerboard pose estimation failed: {exc}") from exc
    if not success:
        raise StereoGeometryError("checkerboard pose estimation returned success=False")
    rotation, _ = cv2.Rodrigues(rvec)
    projected, _ = cv2.projectPoints(objects, rvec, tvec, K, D)
    residuals = np.linalg.norm(projected.reshape(-1, 2) - image, axis=1)
    return CheckerboardPose(rotation, np.asarray(tvec).reshape(3), float(np.sqrt(np.mean(residuals**2))))


def relative_pose_from_checkerboard_poses(
    pose1: CheckerboardPose,
    pose2: CheckerboardPose,
    *,
    baseline_unit: str = "mm",
) -> StereoPose:
    """Convert two metric board poses into ``X2 = R @ X1 + t``."""
    if not isinstance(pose1, CheckerboardPose) or not isinstance(pose2, CheckerboardPose):
        raise TypeError("pose1 and pose2 must be CheckerboardPose instances")
    R21 = pose2.rotation @ pose1.rotation.T
    t21 = pose2.translation - R21 @ pose1.translation
    baseline = float(np.linalg.norm(t21))
    if baseline <= 0:
        raise StereoGeometryError("checkerboard poses imply zero camera displacement")
    return StereoPose(
        rotation=R21,
        translation_unit=t21 / baseline,
        translation_metric=t21,
        essential_matrix=None,
        inlier_mask=np.ones(4, dtype=bool),
        baseline=baseline,
        baseline_unit=baseline_unit,
        scale_source="checkerboard_solvePnP",
        method="checkerboard_pnp",
        median_parallax_degrees=0.0,
    )


def rectify_sequential_views(
    camera_matrix: np.ndarray,
    distortion_coefficients: np.ndarray | None,
    pose: StereoPose,
    image_size: tuple[int, int],
    *,
    alpha: float = 0.0,
    require_metric: bool = True,
) -> RectificationResult:
    """Rectify one sequential pair using its per-pair relative pose."""
    if len(image_size) != 2 or int(image_size[0]) <= 0 or int(image_size[1]) <= 0:
        raise ValueError("image_size must contain positive (width, height)")
    if not -1 <= float(alpha) <= 1:
        raise ValueError("alpha must be between -1 and 1")
    K = validate_camera_matrix(camera_matrix)
    D = validate_distortion_coefficients(distortion_coefficients)
    if not isinstance(pose, StereoPose):
        raise TypeError("pose must be a StereoPose")
    translation = pose.translation_metric if pose.translation_metric is not None else pose.translation_unit
    if require_metric and pose.translation_metric is None:
        raise StereoGeometryError("metric rectification requested without metric translation")
    try:
        R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
            K,
            D,
            K,
            D,
            (int(image_size[0]), int(image_size[1])),
            pose.rotation,
            translation.reshape(3, 1),
            flags=cv2.CALIB_ZERO_DISPARITY,
            alpha=float(alpha),
        )
    except cv2.error as exc:
        raise StereoGeometryError(f"stereo rectification failed: {exc}") from exc
    return RectificationResult(
        R1=np.asarray(R1),
        R2=np.asarray(R2),
        P1=np.asarray(P1),
        P2=np.asarray(P2),
        Q=np.asarray(Q),
        valid_roi1=tuple(int(value) for value in roi1),
        valid_roi2=tuple(int(value) for value in roi2),
    )


def project_points(
    points_3d: np.ndarray,
    camera_matrix: np.ndarray,
    rotation: np.ndarray | None = None,
    translation: np.ndarray | None = None,
    distortion_coefficients: np.ndarray | None = None,
) -> np.ndarray:
    """Project 3D points into an image using the pinhole/distortion model."""
    points = np.asarray(points_3d, dtype=np.float64).reshape(-1, 3)
    if points.shape[0] == 0 or not np.isfinite(points).all():
        raise ValueError("points_3d must contain finite points")
    K = validate_camera_matrix(camera_matrix)
    R = np.eye(3) if rotation is None else _validate_rotation(rotation)
    t = np.zeros(3) if translation is None else np.asarray(translation, dtype=np.float64).reshape(-1)
    if t.shape != (3,) or not np.isfinite(t).all():
        raise ValueError("translation must be a finite length-3 vector")
    rvec, _ = cv2.Rodrigues(R)
    projected, _ = cv2.projectPoints(points, rvec, t.reshape(3, 1), K, validate_distortion_coefficients(distortion_coefficients))
    return projected.reshape(-1, 2)


def triangulate_correspondences(
    points1: np.ndarray,
    points2: np.ndarray,
    camera_matrix: np.ndarray,
    pose: StereoPose,
    *,
    distortion_coefficients: np.ndarray | None = None,
    require_metric: bool = True,
    minimum_parallax_degrees: float = 0.01,
    maximum_reprojection_error_px: float = 5.0,
) -> TriangulationResult:
    """Triangulate paired raw pixels into camera 1's coordinate frame.

    Points are undistorted into pixel coordinates before `cv2.triangulatePoints`. Returned
    reprojection errors are measured in that undistorted pixel coordinate space. Invalid points
    are retained with ``valid_mask=False`` so the caller can show quality evidence rather than
    silently dropping them.
    """
    first, second = validate_correspondences(points1, points2, minimum_count=1)
    if not isinstance(pose, StereoPose):
        raise TypeError("pose must be a StereoPose")
    if not np.isfinite(float(maximum_reprojection_error_px)) or maximum_reprojection_error_px <= 0:
        raise ValueError("maximum_reprojection_error_px must be finite and positive")
    K = validate_camera_matrix(camera_matrix)
    if require_metric and not pose.is_metric:
        raise StereoGeometryError("metric triangulation requested without a physical translation scale")
    first_u = undistort_points_to_pixel(first, K, distortion_coefficients)
    second_u = undistort_points_to_pixel(second, K, distortion_coefficients)
    parallax = _parallax_angles_degrees(first_u, second_u, K, pose.rotation)
    if float(np.median(parallax)) < float(minimum_parallax_degrees):
        raise StereoGeometryError("correspondences have insufficient median triangulation parallax")
    P1, P2 = pose.projection_matrices(K, require_metric=require_metric)
    try:
        homogeneous = cv2.triangulatePoints(P1, P2, first_u.T, second_u.T)
    except cv2.error as exc:
        raise StereoGeometryError(f"triangulation failed: {exc}") from exc
    scale = homogeneous[3]
    finite_scale = np.isfinite(scale) & (np.abs(scale) > 1e-12)
    points_3d = np.full((len(first), 3), np.nan, dtype=np.float64)
    points_3d[finite_scale] = (homogeneous[:3, finite_scale] / scale[finite_scale]).T
    translation = pose.translation_metric if pose.translation_metric is not None else pose.translation_unit
    depth2 = (pose.rotation @ np.nan_to_num(points_3d).T + translation.reshape(3, 1))[2]
    finite_points = np.isfinite(points_3d).all(axis=1)
    positive_depth = finite_points & (points_3d[:, 2] > 0) & (depth2 > 0)
    projected1 = np.full_like(first_u, np.nan)
    projected2 = np.full_like(second_u, np.nan)
    if finite_points.any():
        projected1[finite_points] = project_points(points_3d[finite_points], K)
        projected2[finite_points] = project_points(points_3d[finite_points], K, pose.rotation, translation)
    error1 = np.full(len(first), np.inf, dtype=np.float64)
    error2 = np.full(len(first), np.inf, dtype=np.float64)
    if finite_points.any():
        error1[finite_points] = np.linalg.norm(projected1[finite_points] - first_u[finite_points], axis=1)
        error2[finite_points] = np.linalg.norm(projected2[finite_points] - second_u[finite_points], axis=1)
    valid = (
        positive_depth
        & np.isfinite(error1)
        & np.isfinite(error2)
        & (error1 <= float(maximum_reprojection_error_px))
        & (error2 <= float(maximum_reprojection_error_px))
    )
    unit = pose.baseline_unit if pose.is_metric else None
    return TriangulationResult(
        points_3d=points_3d,
        valid_mask=valid,
        reprojection_error_view1_px=error1,
        reprojection_error_view2_px=error2,
        unit=unit,
        metric=pose.is_metric,
        median_parallax_degrees=float(np.median(parallax)),
    )
