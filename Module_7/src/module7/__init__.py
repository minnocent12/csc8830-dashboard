"""Independent Module 7 calibration and sequential-stereo geometry package."""

from module7.calibration import (
    CalibrationResult,
    calibrate_camera_from_image_paths,
    calibrate_camera_from_points,
    load_calibration,
    save_calibration,
)
from module7.depth_estimation import (
    DepthEstimate,
    depth_from_triangulated_points,
    rectified_depth_from_disparity,
)
from module7.io_utils import read_correspondence_csv
from module7.object_measurement import (
    CircleMeasurement,
    ObjectMeasurementError,
    PolygonMeasurement,
    RectangleMeasurement,
    ReconstructedLandmarks,
    measure_circle,
    measure_circle_from_stereo,
    measure_polygon,
    measure_polygon_from_stereo,
    measure_rectangle,
    measure_rectangle_from_stereo,
    reconstruct_landmarks,
)
from module7.stereo_geometry import (
    StereoPose,
    TriangulationResult,
    estimate_relative_pose,
    triangulate_correspondences,
)

__all__ = [
    "CalibrationResult",
    "CircleMeasurement",
    "DepthEstimate",
    "ObjectMeasurementError",
    "PolygonMeasurement",
    "RectangleMeasurement",
    "ReconstructedLandmarks",
    "StereoPose",
    "TriangulationResult",
    "calibrate_camera_from_image_paths",
    "calibrate_camera_from_points",
    "depth_from_triangulated_points",
    "estimate_relative_pose",
    "load_calibration",
    "measure_circle",
    "measure_circle_from_stereo",
    "measure_polygon",
    "measure_polygon_from_stereo",
    "measure_rectangle",
    "measure_rectangle_from_stereo",
    "reconstruct_landmarks",
    "read_correspondence_csv",
    "rectified_depth_from_disparity",
    "save_calibration",
    "triangulate_correspondences",
]
