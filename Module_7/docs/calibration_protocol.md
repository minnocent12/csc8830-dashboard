# Module 7 Calibration and Sequential-Stereo Capture Protocol

**Status:** Phase 2B capture protocol. Intrinsic calibration is validated from reused Module 2
evidence; no new stereo pose, depth, or physical-validation results are present yet.

This protocol is written for one smartphone camera. It distinguishes the single-camera
intrinsic calibration from the per-capture sequential-stereo pose and metric-scale procedure.

## 1. Required materials and availability

| Material | Status | Requirement |
| --- | --- | --- |
| One smartphone camera | **Confirmed** | Use the same phone for calibration, Q1, and Q3 |
| Printed checkerboard or documented metric target | Pending user acquisition | Square/feature dimensions must be physically measured |
| Ruler or measuring tape | Pending user acquisition | Measure camera displacement, object dimensions, and room dimensions |
| Tripod, mount, slider, or floor marks | Pending user acquisition | Stabilize or repeat camera positions; do not assume ownership |
| Stationary object | Pending user selection | Must remain fixed between sequential views |
| Room access and reference target | Pending user confirmation | Needed for Q3 metric scale and coverage |

If the user cannot obtain a checkerboard, the replacement target and its measured geometry must
be documented and approved before capture. No camera calibration proceeds with an unmeasured
target.

## 2. Smartphone intrinsic calibration

### 2.1 Lock the capture configuration

Record the phone model, camera/lens selection, image resolution, frame orientation, zoom level,
focus behavior, and any available exposure settings. Use the same lens and resolution for all
calibration, Q1, and Q3 captures. If the phone changes resolution, digital zoom, or lens, treat
it as a different calibration condition.

Where the camera application permits it, lock focus and exposure. If it does not, record that
limitation and avoid scenes with changing focus or exposure during the calibration set.

### 2.2 Target and view collection

Use a flat checkerboard with a physically measured square side in millimetres. The target should
fill a useful portion of the frame without being clipped. Collect a diverse set of views rather
than repeated fronto-parallel images:

- centered and off-center views;
- near and far distances within the intended working range;
- left/right and up/down translations;
- moderate rotations about multiple axes;
- all corners visible in every accepted image.

The documented collection recommendation is approximately 15–25 usable views. This is a
coverage recommendation, not a fabricated result or an absolute script requirement: the current
CLI accepts a run only when at least 3 views contain the checkerboard, but a 3-view run should
not automatically be considered adequate for the intended calibration range.

Keep rejected images in a manifest with a reason rather than silently deleting them. The raw
images are source evidence and must not be overwritten.

### 2.3 Implemented computation

`scripts/run_calibration.py` currently:

1. load each image without mutating it;
2. detect the documented inner-corner pattern;
3. refine detected corners to subpixel precision where appropriate;
4. construct object points in a target coordinate frame with `Z=0` and the measured square
   size;
5. estimate the intrinsic matrix `K`, distortion vector `D`, per-view poses, and reprojection
   errors using OpenCV's camera-calibration workflow [OpenCV-Calib];
6. save a provenance record containing image IDs, image size, target dimensions, square size,
   flags, calibration date, and software version;
7. save the calibration JSON without overwriting the originals.

The current CLI does not automatically create corner-overlay figures, a rejected-image manifest,
or a holdout calibration. Those are required review evidence to be recorded manually from the
real capture set or added in a later approved enhancement; their absence must not be hidden.

For a new camera condition, the actual `K`, `D`, and errors remain `PENDING USER EXPERIMENT`
until this script is run on that condition's real images. The current validated record is the
Module 7 recomputation documented in Section 2.5.

### 2.4 Validation

Calibration review must include:

- the actual number of accepted/rejected images;
- per-view and aggregate reprojection error in pixels;
- corner-overlay figures on representative views;
- distortion/undistortion inspection;
- a holdout or repeat-view check where the capture set supports it;
- confirmation that calibration and later object/video resolution match.

No single RMS number is sufficient to prove a useful stereo measurement. The report must discuss
target coverage, corner localization, lens behavior, and the intended working distance.

## 2.5 Phase 2B reuse result

The original Module 2 calibration set was available locally and was reused without modifying
Module 2. The 16 original images were processed directly by Module 7's
`scripts/run_calibration.py` using the recorded 9×6 pattern and 25.0 mm square size. Module 7
accepted all 16 images at 4284×5712 and produced RMS reprojection error 1.84486158434615 px.

The original Module 2 record reports RMS 1.8531894502483754 px. Its intrinsic matrix,
distortion coefficients, image size, target geometry, and per-view errors agree closely with the
Module 7 recomputation. The original Module 2 JSON is not directly loadable by Module 7 because
its field names and metadata schema differ; the native Module 7 recomputation is therefore the
calibration record used for the next stage.

This result validates intrinsic calibration for the recorded iPhone 15 Pro Max lens and
4284×5712 image configuration only. It does not validate sequential pose, metric baseline,
triangulation, or physical depth. Recalibration is required if the stereo capture uses a
different lens, zoom, resolution, orientation pipeline, or materially different camera mode.

## 3. Sequential stereo acquisition for Question 1

### 3.0 Preferred Stage B validation arrangement

For the first physical stereo validation, keep the same 9×6, 25.0 mm checkerboard visible in
both views, together with a stationary textured object or reference. This permits the existing
Module 7 `checkerboard_pnp` mode to detect all 54 corners automatically and recover a metric
relative camera pose from the board geometry. The board's known square size supplies metric scale;
the manually measured camera-center baseline is still required as an independent cross-check,
not as the sole scale source.

The essential-matrix path remains the alternative for later arbitrary object landmarks. It
recovers translation direction only and therefore requires a measured camera-center baseline.

### 3.1 Scene setup

Place the checkerboard on a rigid, flat support and keep it stationary with the object/reference
in the same scene. Mark the first and second phone positions on a surface when practical. Use a
controlled horizontal translation parallel to the checkerboard as the preferred motion, while
keeping the board, object, and relevant landmarks fully visible in both views. Do not assume zero
rotation: the relative rotation is estimated and checked for every pair.

For the recorded calibration focal length of approximately 4,000 pixels and a target around
2–3 m away, a starting translation of roughly 100–200 mm is a theoretical capture recommendation
from `d ≈ fB/Z`. Adjust it to preserve overlap and avoid occlusion; record the actual measured
camera-center displacement rather than treating this recommendation as an experimental result.

The camera-center displacement between the two positions is the baseline magnitude. Measure it
in the selected metric unit and record how the measurement was made. Measuring phone-body edges
instead of optical-center displacement introduces a systematic uncertainty that must be
documented.

### 3.2 Capture sequence

1. Set the phone to the calibrated lens, resolution, zoom, focus, and exposure behavior.
2. Frame the stationary object so required corners or boundary landmarks are visible in both
   views and there is sufficient horizontal parallax.
3. Capture view 1.
4. Move the phone to the marked second position without moving the object or scene.
5. Recheck settings and capture view 2.
6. Record the baseline measurement, approximate motion direction, any support used, and any
   visible scene change.

If the object moves, the settings change, or the scene changes, label the pair invalid for the
primary workflow rather than forcing it through reconstruction.

### 3.3 Pose options

For the checkerboard-visible validation pair, use the implemented `checkerboard_pnp` path:

- detect the 9×6 corners independently in both views;
- pair them by the detector's row-major order, not by guessed pixel coordinates;
- solve the metric checkerboard-to-camera pose in each view with `solvePnP`;
- derive the relative pose and metric translation from the two board poses;
- triangulate the board corners and review board-square distances and reprojection errors.

This is preferable for the first metric validation because it uses 54 known metric target points
and avoids relying on an approximate phone-body translation. It remains sensitive to board
flatness, corner localization, blur, and board visibility, so the measured camera-center baseline
should still be recorded as an independent check.

The essential-matrix alternative is calibrated geometry:

- undistort/normalize verified correspondences;
- estimate the essential matrix with the known intrinsic matrix;
- recover rotation and a unit translation direction;
- scale the direction by the physically measured camera-center displacement;
- select the cheirally valid solution and inspect reprojection error.

If a metric checkerboard is visible in both object views, estimate each camera pose relative to
the board with `solvePnP` and derive the relative pose from the two board poses. This is a
verification/fallback path, not an assumption that a checkerboard will be visible in every
capture.

The workflow must not call `stereoCalibrate` as if two simultaneous rigid cameras existed. A
future implementation may use it only if the actual observations and capture setup satisfy its
assumptions; the one-phone primary path uses per-pair pose recovery instead.

### 3.4 Automatic correspondences

`process_stereo_pair.py --pose-method checkerboard_pnp` does not require a hand-created CSV when
the board is visible in both views. It writes point IDs such as
`checkerboard_r00_c00` through `checkerboard_r05_c08`, together with the detected raw pixel
coordinates, when `--auto-correspondences-output` is supplied. This is the Stage B CSV path.

If arbitrary object landmarks are processed instead, the current essential-mode interface still
requires a user-verified CSV. Those landmarks must be selected from the actual images and must
not be guessed or copied from another pair.

### 3.5 Quality checks

Before triangulation, check:

- same image dimensions and camera configuration;
- enough verified correspondences;
- epipolar residuals and inlier ratio;
- positive-depth/cheirality consistency;
- baseline magnitude and units;
- estimated rotation and translation direction versus the marked motion;
- reprojection error after triangulation;
- sufficient parallax for the intended depth range.

Invalid or weak pairs remain in the manifest with a failure reason. They are not replaced with
invented values.

## 4. Planned persisted outputs

The calibration and pose records defined in `docs/architecture.md` are the minimum schema.
Derived outputs should include:

- calibration metadata and matrices;
- accepted/rejected image manifest;
- corner overlays and reprojection figures;
- stereo pair provenance;
- measured baseline record;
- relative pose and rectification matrices;
- verified correspondence table;
- sparse 3D point table and reprojection errors.

Each output must identify its source images, calibration ID, coordinate frame, unit, software
version, and status (`pending`, `tested`, or `experimentally_validated`).
