"""Metric object dimensions from validated calibrated-stereo landmarks.

This module deliberately keeps reconstruction and dimension estimation separate.  The public
``reconstruct_landmarks`` function calls the existing calibrated-stereo triangulation API and
rejects any non-metric or invalid point before a shape-specific measurement is calculated.
Shape functions then operate only on those validated 3D points in the camera-1 coordinate
frame.  They do not infer dimensions from a single image, a manually entered depth, or a
bounding box.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from module7.depth_estimation import depth_from_triangulated_points
from module7.stereo_geometry import (
    StereoPose,
    TriangulationResult,
    triangulate_correspondences,
    validate_camera_matrix,
)


class ObjectMeasurementError(ValueError):
    """Raised when reconstructed geometry cannot support a shape measurement."""


def _finite_points(points: np.ndarray, *, name: str, dimensions: int) -> np.ndarray:
    array = np.asarray(points, dtype=np.float64).reshape(-1, dimensions)
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one point")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains non-finite values")
    return array.copy()


def _validate_point_ids(point_ids: Sequence[str], count: int) -> tuple[str, ...]:
    identifiers = tuple(str(identifier).strip() for identifier in point_ids)
    if len(identifiers) != count:
        raise ValueError(f"point_ids must contain {count} identifiers, got {len(identifiers)}")
    if any(not identifier for identifier in identifiers):
        raise ValueError("point_ids must not contain empty identifiers")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("point_ids must be unique")
    return identifiers


def _indices_for_ids(landmarks: "ReconstructedLandmarks", selected_ids: Sequence[str]) -> tuple[int, ...]:
    identifiers = tuple(str(identifier).strip() for identifier in selected_ids)
    if len(identifiers) != len(set(identifiers)):
        raise ObjectMeasurementError("selected landmark identifiers must be unique")
    lookup = {identifier: index for index, identifier in enumerate(landmarks.point_ids)}
    missing = [identifier for identifier in identifiers if identifier not in lookup]
    if missing:
        raise ObjectMeasurementError(f"selected landmarks are missing from reconstruction: {missing}")
    return tuple(lookup[identifier] for identifier in identifiers)


def _validate_fraction(value: float | None, *, name: str) -> float | None:
    if value is None:
        return None
    fraction = float(value)
    if not np.isfinite(fraction) or fraction < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return fraction


@dataclass(frozen=True)
class ReconstructedLandmarks:
    """Metric 3D landmarks and the stereo evidence used to recover them."""

    point_ids: tuple[str, ...]
    points_view1: np.ndarray
    points_view2: np.ndarray
    points_3d: np.ndarray
    depths: np.ndarray
    triangulation: TriangulationResult

    def __post_init__(self) -> None:
        identifiers = _validate_point_ids(self.point_ids, len(self.point_ids))
        first = _finite_points(self.points_view1, name="points_view1", dimensions=2)
        second = _finite_points(self.points_view2, name="points_view2", dimensions=2)
        points = _finite_points(self.points_3d, name="points_3d", dimensions=3)
        depths = _finite_points(self.depths, name="depths", dimensions=1).reshape(-1)
        count = len(identifiers)
        if first.shape[0] != count or second.shape[0] != count or points.shape[0] != count or depths.size != count:
            raise ValueError("landmark arrays must have the same number of entries as point_ids")
        if not isinstance(self.triangulation, TriangulationResult):
            raise TypeError("triangulation must be a TriangulationResult")
        if not self.triangulation.metric or self.triangulation.unit not in {"m", "mm"}:
            raise ObjectMeasurementError("landmarks must come from metric triangulation in metres or millimetres")
        if self.triangulation.points_3d.shape != points.shape:
            raise ValueError("points_3d must match triangulation.points_3d")
        if not np.allclose(self.triangulation.points_3d, points, equal_nan=False):
            raise ValueError("points_3d must match triangulation.points_3d")
        if not np.isfinite(depths).all() or not (depths > 0).all():
            raise ObjectMeasurementError("landmarks must have finite positive camera-1 depths")
        object.__setattr__(self, "point_ids", identifiers)
        object.__setattr__(self, "points_view1", first)
        object.__setattr__(self, "points_view2", second)
        object.__setattr__(self, "points_3d", points)
        object.__setattr__(self, "depths", depths)

    @property
    def unit(self) -> str:
        """Physical unit attached by the metric stereo pose."""
        return str(self.triangulation.unit)

    def to_dict(self) -> dict[str, object]:
        """Return an auditable JSON-compatible reconstruction record."""
        return {
            "point_ids": list(self.point_ids),
            "points_view1": self.points_view1.tolist(),
            "points_view2": self.points_view2.tolist(),
            "points_3d": self.points_3d.tolist(),
            "depths": self.depths.tolist(),
            "unit": self.unit,
            "stereo_quality": {
                "valid_mask": self.triangulation.valid_mask.tolist(),
                "reprojection_error_view1_px": self.triangulation.reprojection_error_view1_px.tolist(),
                "reprojection_error_view2_px": self.triangulation.reprojection_error_view2_px.tolist(),
                "median_parallax_degrees": self.triangulation.median_parallax_degrees,
                "metric": self.triangulation.metric,
            },
        }


def reconstruct_landmarks(
    point_ids: Sequence[str],
    points_view1: np.ndarray,
    points_view2: np.ndarray,
    camera_matrix: np.ndarray,
    pose: StereoPose,
    *,
    distortion_coefficients: np.ndarray | None = None,
    minimum_parallax_degrees: float = 0.01,
    maximum_reprojection_error_px: float = 5.0,
) -> ReconstructedLandmarks:
    """Recover metric 3D landmarks before any shape dimension is calculated.

    The existing ``triangulate_correspondences`` implementation supplies undistortion,
    metric projection matrices, cheirality, parallax, and reprojection checks.  This wrapper
    converts its quality mask into a hard measurement gate: a shape dimension is never
    calculated from a partially invalid landmark set.
    """
    first = _finite_points(points_view1, name="points_view1", dimensions=2)
    second = _finite_points(points_view2, name="points_view2", dimensions=2)
    if first.shape != second.shape:
        raise ValueError("points_view1 and points_view2 must have the same shape")
    identifiers = _validate_point_ids(point_ids, first.shape[0])
    validate_camera_matrix(camera_matrix)
    triangulation = triangulate_correspondences(
        first,
        second,
        camera_matrix,
        pose,
        distortion_coefficients=distortion_coefficients,
        require_metric=True,
        minimum_parallax_degrees=minimum_parallax_degrees,
        maximum_reprojection_error_px=maximum_reprojection_error_px,
    )
    if not triangulation.metric or triangulation.unit not in {"m", "mm"}:
        raise ObjectMeasurementError("metric stereo reconstruction is required before dimension estimation")
    if not bool(np.all(triangulation.valid_mask)):
        invalid = [identifier for identifier, valid in zip(identifiers, triangulation.valid_mask, strict=True) if not valid]
        raise ObjectMeasurementError(
            "stereo quality checks rejected landmarks; no dimension was calculated for: "
            f"{invalid}"
        )
    depth = depth_from_triangulated_points(triangulation.points_3d, unit=triangulation.unit)
    return ReconstructedLandmarks(
        point_ids=identifiers,
        points_view1=first,
        points_view2=second,
        points_3d=triangulation.points_3d,
        depths=depth.depth,
        triangulation=triangulation,
    )


def _plane_metrics(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, np.ndarray]:
    """Fit a least-squares plane and return origin, basis, normal, RMS/max residual, singular values."""
    if points.shape[0] < 3:
        raise ObjectMeasurementError("at least three 3D points are required for plane geometry")
    origin = points.mean(axis=0)
    centered = points - origin
    _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    scale = max(float(singular_values[0]), np.finfo(np.float64).eps)
    if singular_values.size < 2 or float(singular_values[1]) <= scale * 1e-10:
        raise ObjectMeasurementError("3D landmarks are collinear; plane/circle geometry is undefined")
    normal = vh[-1]
    normal /= np.linalg.norm(normal)
    residuals = np.abs(centered @ normal)
    basis = np.vstack((vh[0], vh[1]))
    return origin, basis, normal, float(np.sqrt(np.mean(residuals**2))), float(np.max(residuals)), singular_values


def _edge_lengths(points: np.ndarray, *, closed: bool) -> np.ndarray:
    if points.shape[0] < (3 if closed else 2):
        minimum = 3 if closed else 2
        raise ObjectMeasurementError(f"at least {minimum} vertices are required")
    endpoint = np.roll(points, -1, axis=0) if closed else points[1:]
    start = points if closed else points[:-1]
    lengths = np.linalg.norm(endpoint - start, axis=1)
    if not np.isfinite(lengths).all() or np.any(lengths <= np.finfo(np.float64).eps):
        raise ObjectMeasurementError("shape contains a zero-length or invalid edge")
    return lengths


def _measurement_ids(landmarks: ReconstructedLandmarks, selected_ids: Sequence[str]) -> tuple[tuple[str, ...], np.ndarray]:
    identifiers = tuple(str(identifier).strip() for identifier in selected_ids)
    if any(not identifier for identifier in identifiers):
        raise ObjectMeasurementError("selected landmark identifiers must not be empty")
    indices = _indices_for_ids(landmarks, identifiers)
    return identifiers, landmarks.points_3d[list(indices)]


@dataclass(frozen=True)
class RectangleMeasurement:
    """Width and height estimated from four ordered 3D rectangle corners."""

    corner_ids: tuple[str, str, str, str]
    corners_3d: np.ndarray
    unit: str
    width: float
    height: float
    width_edge_lengths: tuple[float, float]
    height_edge_lengths: tuple[float, float]
    planarity_rms: float
    planarity_max: float
    right_angle_deviations_degrees: tuple[float, ...]
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "shape": "rectangle",
            "corner_ids": list(self.corner_ids),
            "corners_3d": self.corners_3d.tolist(),
            "unit": self.unit,
            "dimensions": {"width": self.width, "height": self.height},
            "opposite_edge_lengths": {
                "width": list(self.width_edge_lengths),
                "height": list(self.height_edge_lengths),
            },
            "quality": {
                "planarity_rms": self.planarity_rms,
                "planarity_max": self.planarity_max,
                "right_angle_deviations_degrees": list(self.right_angle_deviations_degrees),
            },
            "assumptions": list(self.assumptions),
        }


def measure_rectangle(
    landmarks: ReconstructedLandmarks,
    corner_ids: Sequence[str],
    *,
    max_opposite_edge_disagreement_fraction: float = 0.05,
    max_planarity_fraction: float = 0.05,
    max_right_angle_deviation_degrees: float = 15.0,
) -> RectangleMeasurement:
    """Measure a rectangle from ordered ``top-left, top-right, bottom-right, bottom-left`` 3D corners."""
    if len(corner_ids) != 4:
        raise ValueError("rectangle corner_ids must contain four ordered corners")
    disagreement_limit = _validate_fraction(
        max_opposite_edge_disagreement_fraction,
        name="max_opposite_edge_disagreement_fraction",
    )
    planarity_limit = _validate_fraction(max_planarity_fraction, name="max_planarity_fraction")
    angle_limit = float(max_right_angle_deviation_degrees)
    if not np.isfinite(angle_limit) or angle_limit < 0:
        raise ValueError("max_right_angle_deviation_degrees must be finite and non-negative")
    identifiers, corners = _measurement_ids(landmarks, corner_ids)
    edges = _edge_lengths(corners, closed=True)
    width_edges = (float(edges[0]), float(edges[2]))
    height_edges = (float(edges[1]), float(edges[3]))
    width = float(np.mean(width_edges))
    height = float(np.mean(height_edges))
    width_disagreement = abs(width_edges[0] - width_edges[1]) / width
    height_disagreement = abs(height_edges[0] - height_edges[1]) / height
    if disagreement_limit is not None and max(width_disagreement, height_disagreement) > disagreement_limit:
        raise ObjectMeasurementError(
            "opposite rectangle edges disagree beyond the configured quality limit: "
            f"width={width_disagreement:.6g}, height={height_disagreement:.6g}"
        )
    _, _, _, planarity_rms, planarity_max, _ = _plane_metrics(corners)
    if planarity_limit is not None and planarity_max > planarity_limit * max(width, height):
        raise ObjectMeasurementError(
            "rectangle corners are not sufficiently coplanar for the configured quality limit"
        )
    deviations: list[float] = []
    for index in range(4):
        previous = corners[(index - 1) % 4] - corners[index]
        following = corners[(index + 1) % 4] - corners[index]
        cosine = float(np.dot(previous, following) / (np.linalg.norm(previous) * np.linalg.norm(following)))
        angle = float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))
        deviations.append(abs(angle - 90.0))
    if max(deviations) > angle_limit:
        raise ObjectMeasurementError(
            "rectangle corner angles exceed the configured right-angle quality limit: "
            f"max deviation={max(deviations):.6g} degrees"
        )
    return RectangleMeasurement(
        corner_ids=(identifiers[0], identifiers[1], identifiers[2], identifiers[3]),
        corners_3d=corners,
        unit=landmarks.unit,
        width=width,
        height=height,
        width_edge_lengths=width_edges,
        height_edge_lengths=height_edges,
        planarity_rms=planarity_rms,
        planarity_max=planarity_max,
        right_angle_deviations_degrees=tuple(deviations),
        assumptions=(
            "four selected landmarks are ordered top-left, top-right, bottom-right, bottom-left",
            "the physical object face is modeled as a planar rectangle",
            "reported width and height are means of opposite reconstructed 3D edges",
        ),
    )


@dataclass(frozen=True)
class CircleMeasurement:
    """Diameter estimated by fitting a 3D circle to reconstructed boundary landmarks."""

    boundary_ids: tuple[str, ...]
    boundary_points_3d: np.ndarray
    center_3d: np.ndarray
    unit: str
    radius: float
    diameter: float
    plane_normal: np.ndarray
    planarity_rms: float
    planarity_max: float
    fit_rms: float
    fit_max: float
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "shape": "circle",
            "boundary_ids": list(self.boundary_ids),
            "boundary_points_3d": self.boundary_points_3d.tolist(),
            "center_3d": self.center_3d.tolist(),
            "unit": self.unit,
            "dimensions": {"radius": self.radius, "diameter": self.diameter},
            "plane_normal": self.plane_normal.tolist(),
            "quality": {
                "planarity_rms": self.planarity_rms,
                "planarity_max": self.planarity_max,
                "circle_fit_rms": self.fit_rms,
                "circle_fit_max": self.fit_max,
            },
            "assumptions": list(self.assumptions),
        }


def measure_circle(
    landmarks: ReconstructedLandmarks,
    boundary_ids: Sequence[str],
    *,
    max_planarity_fraction: float = 0.05,
    max_fit_residual_fraction: float = 0.05,
) -> CircleMeasurement:
    """Fit a circle in the recovered 3D boundary plane and report its metric diameter."""
    if len(boundary_ids) < 3:
        raise ValueError("circle boundary_ids must contain at least three points")
    planarity_limit = _validate_fraction(max_planarity_fraction, name="max_planarity_fraction")
    fit_limit = _validate_fraction(max_fit_residual_fraction, name="max_fit_residual_fraction")
    identifiers, boundary = _measurement_ids(landmarks, boundary_ids)
    origin, basis, normal, planarity_rms, planarity_max, _ = _plane_metrics(boundary)
    xy = (boundary - origin) @ basis.T
    design = np.column_stack((2.0 * xy[:, 0], 2.0 * xy[:, 1], np.ones(len(xy))))
    values = np.sum(xy**2, axis=1)
    coefficients, _, rank, _ = np.linalg.lstsq(design, values, rcond=None)
    if rank < 3 or not np.isfinite(coefficients).all():
        raise ObjectMeasurementError("circle fit is rank-deficient; boundary landmarks are insufficient")
    center_2d = coefficients[:2]
    radius_squared = float(np.dot(center_2d, center_2d) + coefficients[2])
    if not np.isfinite(radius_squared) or radius_squared <= np.finfo(np.float64).eps:
        raise ObjectMeasurementError("circle fit produced a non-positive radius")
    radius = float(np.sqrt(radius_squared))
    center_3d = origin + center_2d[0] * basis[0] + center_2d[1] * basis[1]
    radial_residuals = np.abs(np.linalg.norm(boundary - center_3d, axis=1) - radius)
    fit_rms = float(np.sqrt(np.mean(radial_residuals**2)))
    fit_max = float(np.max(radial_residuals))
    reference_scale = max(radius, np.finfo(np.float64).eps)
    if planarity_limit is not None and planarity_max > planarity_limit * reference_scale:
        raise ObjectMeasurementError("circle boundary is not sufficiently coplanar for the configured quality limit")
    if fit_limit is not None and fit_max > fit_limit * reference_scale:
        raise ObjectMeasurementError("circle boundary residual exceeds the configured circle-fit quality limit")
    return CircleMeasurement(
        boundary_ids=identifiers,
        boundary_points_3d=boundary,
        center_3d=center_3d,
        unit=landmarks.unit,
        radius=radius,
        diameter=2.0 * radius,
        plane_normal=normal,
        planarity_rms=planarity_rms,
        planarity_max=planarity_max,
        fit_rms=fit_rms,
        fit_max=fit_max,
        assumptions=(
            "selected landmarks are corresponding points on the visible circular boundary",
            "the physical circular object is rigid and its boundary lies on one plane",
            "a least-squares circle is fit in the recovered 3D object plane",
        ),
    )


@dataclass(frozen=True)
class PolygonMeasurement:
    """Visible polygon edge lengths from reconstructed vertices in boundary order."""

    vertex_ids: tuple[str, ...]
    vertices_3d: np.ndarray
    edge_lengths: tuple[float, ...]
    unit: str
    closed: bool
    planarity_rms: float | None
    planarity_max: float | None
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "shape": "polygon",
            "vertex_ids": list(self.vertex_ids),
            "vertices_3d": self.vertices_3d.tolist(),
            "unit": self.unit,
            "closed": self.closed,
            "dimensions": {f"edge_{index + 1}": length for index, length in enumerate(self.edge_lengths)},
            "edge_lengths": list(self.edge_lengths),
            "quality": {
                "planarity_rms": self.planarity_rms,
                "planarity_max": self.planarity_max,
            },
            "assumptions": list(self.assumptions),
        }


def measure_polygon(
    landmarks: ReconstructedLandmarks,
    vertex_ids: Sequence[str],
    *,
    closed: bool = True,
    require_planar: bool = False,
    max_planarity_fraction: float = 0.05,
) -> PolygonMeasurement:
    """Measure each visible adjacent polygon edge from ordered 3D vertices.

    Edge lengths remain valid 3D measurements even when ``require_planar=False``.  Planarity
    is reported as a diagnostic and can be made a hard quality gate when the physical polygon
    model requires a single plane.
    """
    if len(vertex_ids) < (3 if closed else 2):
        minimum = 3 if closed else 2
        raise ValueError(f"polygon vertex_ids must contain at least {minimum} vertices")
    planarity_limit = _validate_fraction(max_planarity_fraction, name="max_planarity_fraction")
    identifiers, vertices = _measurement_ids(landmarks, vertex_ids)
    edge_lengths = _edge_lengths(vertices, closed=closed)
    planarity_rms: float | None = None
    planarity_max: float | None = None
    if len(vertices) >= 3:
        _, _, _, planarity_rms, planarity_max, _ = _plane_metrics(vertices)
        scale = max(float(np.max(edge_lengths)), np.finfo(np.float64).eps)
        if require_planar and planarity_limit is not None and planarity_max > planarity_limit * scale:
            raise ObjectMeasurementError("polygon vertices are not sufficiently coplanar for the configured quality limit")
    return PolygonMeasurement(
        vertex_ids=identifiers,
        vertices_3d=vertices,
        edge_lengths=tuple(float(length) for length in edge_lengths),
        unit=landmarks.unit,
        closed=bool(closed),
        planarity_rms=planarity_rms,
        planarity_max=planarity_max,
        assumptions=(
            "selected landmarks are corresponding visible vertices in boundary order",
            "each reported length is the Euclidean distance between adjacent reconstructed vertices",
            "no bounding-box dimension is substituted for a polygon edge",
        )
        + (("vertices are required to be approximately coplanar",) if require_planar else ()),
    )


def measure_rectangle_from_stereo(
    point_ids: Sequence[str],
    points_view1: np.ndarray,
    points_view2: np.ndarray,
    camera_matrix: np.ndarray,
    pose: StereoPose,
    corner_ids: Sequence[str],
    **kwargs: object,
) -> tuple[ReconstructedLandmarks, RectangleMeasurement]:
    """Reconstruct landmarks, then measure a rectangle from the recovered 3D points."""
    landmarks = reconstruct_landmarks(point_ids, points_view1, points_view2, camera_matrix, pose, **kwargs)
    return landmarks, measure_rectangle(landmarks, corner_ids)


def measure_circle_from_stereo(
    point_ids: Sequence[str],
    points_view1: np.ndarray,
    points_view2: np.ndarray,
    camera_matrix: np.ndarray,
    pose: StereoPose,
    boundary_ids: Sequence[str],
    **kwargs: object,
) -> tuple[ReconstructedLandmarks, CircleMeasurement]:
    """Reconstruct landmarks, then fit a 3D circle and measure its diameter."""
    landmarks = reconstruct_landmarks(point_ids, points_view1, points_view2, camera_matrix, pose, **kwargs)
    return landmarks, measure_circle(landmarks, boundary_ids)


def measure_polygon_from_stereo(
    point_ids: Sequence[str],
    points_view1: np.ndarray,
    points_view2: np.ndarray,
    camera_matrix: np.ndarray,
    pose: StereoPose,
    vertex_ids: Sequence[str],
    **kwargs: object,
) -> tuple[ReconstructedLandmarks, PolygonMeasurement]:
    """Reconstruct landmarks, then measure each visible polygon edge."""
    landmarks = reconstruct_landmarks(point_ids, points_view1, points_view2, camera_matrix, pose, **kwargs)
    return landmarks, measure_polygon(landmarks, vertex_ids)
