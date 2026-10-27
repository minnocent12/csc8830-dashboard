"""Depth calculations and quality summaries for Module 7."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DepthEstimate:
    """Depth values with explicit validity flags and provenance."""

    depth: np.ndarray
    valid_mask: np.ndarray
    unit: str | None
    source: str

    def __post_init__(self) -> None:
        depth = np.asarray(self.depth, dtype=np.float64).reshape(-1)
        valid = np.asarray(self.valid_mask, dtype=bool).reshape(-1)
        if depth.shape != valid.shape:
            raise ValueError("depth and valid_mask must have the same shape")
        object.__setattr__(self, "depth", depth)
        object.__setattr__(self, "valid_mask", valid)

    @property
    def valid_depth(self) -> np.ndarray:
        """Return finite positive depths that passed validation."""
        return self.depth[self.valid_mask]


def rectified_depth_from_disparity(
    focal_length_px: float,
    baseline: float,
    disparity_px: np.ndarray,
    *,
    unit: str,
    allow_invalid: bool = False,
) -> DepthEstimate:
    """Compute ``Z = fB/d`` under the ideal rectified-parallel-stereo assumptions.

    This formula is valid only for a rectified pair with a known metric baseline and positive
    nonzero disparity. Invalid entries are either rejected or returned as NaN with a false mask.
    The actual sequential-stereo reconstruction should prefer calibrated triangulation.
    """
    focal = float(focal_length_px)
    scale = float(baseline)
    if not np.isfinite(focal) or focal <= 0:
        raise ValueError("focal_length_px must be finite and positive")
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("baseline must be finite and positive")
    if unit not in {"m", "mm"}:
        raise ValueError("unit must be 'm' or 'mm'")
    disparity = np.asarray(disparity_px, dtype=np.float64).reshape(-1)
    if disparity.size == 0:
        raise ValueError("disparity_px must contain at least one value")
    valid = np.isfinite(disparity) & (disparity > 0)
    if not allow_invalid and not np.all(valid):
        raise ValueError("disparity must be finite and positive for Z=fB/d")
    depth = np.full(disparity.shape, np.nan, dtype=np.float64)
    depth[valid] = focal * scale / disparity[valid]
    return DepthEstimate(depth, valid, unit, "rectified_disparity_formula")


def depth_from_triangulated_points(
    points_3d: np.ndarray,
    *,
    unit: str | None,
    allow_invalid: bool = False,
) -> DepthEstimate:
    """Extract camera-1 forward depth ``Z`` from triangulated ``(X,Y,Z)`` points."""
    points = np.asarray(points_3d, dtype=np.float64).reshape(-1, 3)
    if points.shape[0] == 0:
        raise ValueError("points_3d must contain at least one point")
    valid = np.isfinite(points).all(axis=1) & (points[:, 2] > 0)
    if not allow_invalid and not np.all(valid):
        raise ValueError("triangulated points contain non-finite or non-positive depths")
    depth = np.full(points.shape[0], np.nan, dtype=np.float64)
    depth[np.isfinite(points).all(axis=1)] = points[np.isfinite(points).all(axis=1), 2]
    return DepthEstimate(depth, valid, unit, "triangulated_camera1_Z")


def summarize_depth(depth_estimate: DepthEstimate) -> dict[str, float | int | str | None]:
    """Return descriptive values for valid depth entries only."""
    if not isinstance(depth_estimate, DepthEstimate):
        raise TypeError("depth_estimate must be a DepthEstimate")
    values = depth_estimate.valid_depth
    summary: dict[str, float | int | str | None] = {
        "source": depth_estimate.source,
        "unit": depth_estimate.unit,
        "count": int(values.size),
        "invalid_count": int(depth_estimate.depth.size - values.size),
    }
    if values.size:
        summary.update(
            minimum=float(values.min()),
            maximum=float(values.max()),
            mean=float(values.mean()),
        )
    else:
        summary.update(minimum=None, maximum=None, mean=None)
    return summary
