# Module 7 Technical Architecture

**Status:** Implemented calibrated-stereo core and standalone Question 1 webpage; Phase 4 and
public deployment remain out of scope.

This architecture preserves Module 7 independence while following the source-layout,
Streamlit page-provider, testing, data, and documentation patterns observed in Modules 2–6.
The design is adapted to the confirmed hardware constraint: **one smartphone camera**.

## 1. Confirmed decisions and open dependencies

| Item | Status | Design consequence |
| --- | --- | --- |
| Camera | Confirmed: one smartphone camera | Q1 uses sequential calibrated stereo; Q3 uses calibrated moving-camera video |
| Tripod/mount or slider | Not confirmed | Capture protocol must support floor marks and careful manual translation if no mount is available |
| Printed checkerboard | Recommended, not confirmed | Required before real calibration; square size must be physically measured |
| Ruler/tape measure | Recommended, not confirmed | Needed for the Q1 camera displacement and independent object/room validation |
| Stationary validation objects | Not confirmed | Needed for real Q1 validation; no dimensions may be invented |
| Public sample data | Proposed local bundle only | Publication approval is pending; original captures remain separate |
| Module 7 Git repository | Initialized locally on `task/module-7-initial-repository` | No commit, remote, push, or deployment has occurred |

## 2. Target package layout

```text
Module_7/
├── app.py                         # thin standalone Streamlit entry point
├── pyproject.toml                 # independent package/dependencies
├── .streamlit/config.toml         # generated csc8830-ui 0.6.0 theme
├── data/
│   ├── calibration/               # raw calibration captures; policy-controlled
│   ├── stereo_pairs/              # sequential left/right object captures
│   ├── objects/                   # object metadata and selected captures
│   └── room_videos/               # smartphone video and frame metadata
├── docs/
│   ├── architecture.md
│   ├── calibration_protocol.md
│   ├── experimental_protocol.md
│   ├── uncalibrated_stereo_derivation.md
│   ├── references.md
│   └── report/
├── results/
│   ├── calibration/
│   ├── object_measurements/
│   └── room_measurements/
├── scripts/                       # reproducible command-line workflows
├── src/module7/
│   ├── calibration.py
│   ├── stereo_geometry.py
│   ├── depth_estimation.py
│   ├── object_measurement.py
│   ├── room_measurement.py         # reserved for separately authorized Phase 4 work
│   ├── validation.py
│   ├── visualization.py
│   └── webapp/
│       ├── _page.py
│       ├── registry.py
│       ├── shell.py
│       ├── ui.py
│       ├── pages.py
│       └── design/                # vendored csc8830-ui 0.6.0 components
├── data/proposed_public_demo/      # manifest-defined runtime bundle; publication pending
│   ├── manifest.json
│   ├── images/
│   └── records/
└── tests/
```

Core modules must not import Streamlit. The web layer may call core functions and render their
returned records, images, tables, and warnings. Module 7 must not import runtime code from
Modules 2–6.

The implemented standalone page provider is `module7.webapp.pages.get_pages()`. Its pages use
the same calibrated-stereo records and saved diagnostics as the command-line workflows. The
vendored design package supplies the shell, navigation, headers, image comparisons, metric rows,
status banners, and result sections. The standalone runtime reads the manifest-defined curated
bundle for its saved examples. The bundle is review-only and is not a publication approval
decision. Original captures and full result records remain separate local evidence and are not
required to launch the standalone app.

## 3. Coordinate systems and geometry conventions

### 3.1 Image coordinates

- Raw image coordinates are `(u, v)` in pixels, with `u` increasing rightward and `v`
  increasing downward.
- Raw images retain lens distortion. Rectified images are a derived output and never replace
  the original input.
- Every point record stores `image_id`, `coordinate_space` (`raw` or `rectified`), pixel
  coordinates, and image dimensions.

### 3.2 OpenCV camera coordinates

Use the conventional camera frame: `X` right, `Y` down, and `Z` forward from the camera. For a
single calibrated smartphone, the intrinsic matrix and distortion vector are:

```text
K = [[fx,  0, cx],
     [ 0, fy, cy],
     [ 0,  0,  1]]

D = [k1, k2, p1, p2, k3, ...]
```

The actual entries in `K` and `D` are produced only by the user's calibration images. They are
not defaults and must never be hardcoded.

### 3.3 Sequential stereo frame

For Q1, view 1 is the reference camera frame:

```text
X1 = [X1, Y1, Z1]^T
P1 = K [I | 0]
```

The second phone position is represented by the change of basis:

```text
X2 = R X1 + t_metric
P2 = K [R | t_metric]
```

The camera-center displacement is

```text
C2_in_frame_1 = -R^T t_metric
B = ||C2_in_frame_1|| = ||t_metric||
```

where `B` is the physically measured camera-center displacement in the selected metric unit.
The essential-matrix pose estimate supplies `R` and a translation direction; the measured
displacement supplies its metric scale. The sign is selected using cheirality/reprojection
checks, never by an arbitrary sign assumption.

### 3.4 Room world frame

For Q3's minimum viable reference-assisted workflow, define a metric room frame from a fixed,
measured reference target or surveyed reference geometry:

- origin: a documented target corner or room reference point;
- axes: target horizontal axis, target vertical/normal convention, and a documented third axis;
- unit: millimetres or metres, recorded in metadata;
- room planes: floor, walls, and ceiling represented by fitted plane equations in this frame.

The reference target is not a fabricated scale source. Its dimensions must be measured or come
from a documented physical specification, and its visible corners must be observed in the
recorded video frames used to establish metric pose.

## 4. Data contracts

The following are design schemas, not populated experimental results. JSON/YAML serialization
may be selected during implementation, but the fields and units must remain explicit.

### 4.1 Calibration record

```text
CalibrationRecord
  calibration_id: string
  camera_make_model: string | null
  lens_or_camera_mode: string
  image_width_px: integer
  image_height_px: integer
  target_type: "checkerboard" | other documented target
  target_columns: integer
  target_rows: integer
  square_size_mm: real
  image_ids: list[string]
  intrinsic_matrix_K: 3x3 real matrix
  distortion_coefficients_D: real vector
  per_view_rms_px: list[real]
  aggregate_rms_px: real
  flags: list[string]
  created_at: string
  source_manifest: string
  status: "pending" | "tested" | "experimentally_validated"
```

`K`, `D`, RMS errors, and target information remain pending until a real calibration run.

### 4.2 Sequential stereo pose record

```text
StereoPoseRecord
  stereo_id: string
  calibration_id: string
  view1_image_id: string
  view2_image_id: string
  image_size_px: [integer, integer]
  baseline_magnitude: real
  baseline_unit: "m" | "mm"
  baseline_measurement_method: string
  rotation_R_2_from_1: 3x3 real matrix
  translation_direction_unit_2_from_1: length-3 real vector
  translation_metric_2_from_1: length-3 real vector
  pose_method: "essential_matrix_scaled_by_measured_baseline" | "checkerboard_pnp"
  inlier_count: integer
  reprojection_error_px: real
  cheirality_passed: boolean
  rectification_metadata: object
  status: "pending" | "tested" | "experimentally_validated"
```

The record must state whether the baseline was measured between optical centers or only
approximated from phone position marks. Approximate values cannot be presented as validated
metric results.

### 4.3 Correspondence and 3D point records

```text
Correspondence
  point_id: string
  semantic_label: string
  view1_pixel_uv: [real, real]
  view2_pixel_uv: [real, real]
  coordinate_space: "raw" | "rectified"
  source: "manual" | "feature_candidate_then_verified"
  inlier: boolean
  disparity_px: real | null
  quality_note: string

Point3D
  point_id: string
  xyz: [real, real, real]
  unit: "m" | "mm"
  reconstruction_method: "triangulatePoints" | "reprojectImageTo3D"
  reprojection_error_px: real
  positive_depth_both_views: boolean
  valid: boolean
```

Manual landmark selection is the first implementation path because every measurement endpoint
can be explained to a grader. Automatic matching may propose candidates but cannot silently
replace human verification.

### 4.4 Object measurement record

```text
ObjectMeasurement
  measurement_id: string
  object_id: string
  shape: "rectangle" | "circle" | "polygon"
  stereo_id: string
  landmark_ids_in_boundary_order: list[string]
  dimensions: list[{name: string, value: real, unit: string}]
  physical_reference: object | null
  absolute_error: object | null
  percentage_error: object | null
  quality_notes: list[string]
  status: "pending" | "tested" | "experimentally_validated"
```

Rectangle dimensions are Euclidean lengths between reconstructed corners. A polygon reports
each visible boundary edge. A circle reports a diameter only after the documented planar,
visibility, correspondence, and circularity assumptions pass.

### 4.5 Room measurement record

```text
RoomMeasurement
  room_id: string
  video_id: string
  calibration_id: string
  reference_id: string
  selected_frame_ids: list[integer]
  tracked_landmark_count: integer
  reconstructed_point_count: integer
  plane_fit_records: list[{plane: string, equation: object, residual: real}]
  dimensions: {length: real | null, width: real | null, height: real | null}
  unit: "m" | "mm"
  physical_reference: {length: real | null, width: real | null, height: real | null}
  errors: object | null
  coverage_notes: list[string]
  status: "pending" | "tested" | "experimentally_validated"
```

## 5. Question 1 architecture: one-phone sequential calibrated stereo

### 5.1 Primary pose method

The primary first implementation is **calibrated essential-matrix geometry scaled by a
physically measured camera-center displacement**:

1. Calibrate the smartphone intrinsics once for the exact camera mode and resolution.
2. Place the stationary object in a fixed scene. Mark two phone positions and measure the
   displacement between the optical centers as accurately as the available equipment allows.
3. Capture view 1 and view 2 without moving the object. Keep lens, resolution, zoom, focus, and
   exposure behavior consistent.
4. Undistort or normalize verified correspondences using the single-camera calibration.
5. Estimate `E` with calibrated correspondences and recover `R` plus a unit translation
   direction with an essential-matrix method. Select the physically consistent solution using
   positive depth and reprojection checks.
6. Scale the translation direction by the measured baseline magnitude to form `t_metric`.
7. Rectify the pair with the per-pair `R` and `t_metric` when rectification improves the
   correspondence display. Use the resulting projection matrices for sparse triangulation.
8. Reconstruct each object landmark and calculate dimensions from the recovered 3D coordinates.

This is not a permanent synchronized stereo rig and is not treated as one. `stereoCalibrate`
is not blindly applied to two unrelated smartphone positions. If the real capture includes a
metric checkerboard visible in both views, a checkerboard-pose method may replace or verify the
essential-matrix pose.

### 5.2 Alternative pose methods

| Method | Assumptions | Precision/practicality | Failure case | Decision |
| --- | --- | --- | --- | --- |
| Essential matrix + measured displacement | Intrinsics known; enough inlier correspondences; measured camera-center displacement gives scale | Works with one phone and no board in object view; rotation and direction are estimated per pair | Low texture, small parallax, inaccurate baseline, wrong sign, pose degeneracy | **Primary first implementation** |
| Checkerboard `solvePnP` in both views | Same metric checkerboard is visible in both images; board dimensions are known | Direct metric pose per image; very explainable | Board occluded, too small, or not in object capture | Verification/fallback when practical |
| Controlled translation with assumed parallel views | Phone orientation remains fixed and translation is measured | Simple and interpretable; useful for teaching `Z=fB/d` | Handheld rotation violates the model; inaccurate parallelism | Acquisition preference, not an unverified assumption |
| `stereoCalibrate` as a two-camera rig calibration | Two camera streams observe the same calibration target as a fixed pair | Appropriate for rigid dual-camera stereo, not the one-phone capture by itself | Misleading if sequential views are treated as simultaneous cameras | Not primary; may be used only if actual observations justify it |

### 5.3 Depth precision and rejection rules

Depth uncertainty increases when the baseline is small, disparity is small, image localization is
uncertain, or the pose is inaccurate. The implementation must flag rather than hide:

- zero, negative, non-finite, or implausibly small disparity;
- correspondence pairs that fail an epipolar/reprojection check;
- points with negative depth in either camera frame;
- excessive reprojection error;
- insufficient parallax or too few inliers;
- image resolution/lens/zoom mismatch;
- visible object motion or scene changes between captures.

## 6. Question 3 architecture: calibrated moving-camera smartphone video

### 6.1 Minimum viable approach

The minimum viable workflow is **reference-assisted sparse multiview measurement**, not a claim
of general-purpose monocular room scanning:

1. Calibrate the smartphone intrinsics at the video resolution.
2. Fix a physically measured planar target or other known-length reference in the room. The
   target's coordinates and dimensions define the metric room frame.
3. Record a slow video path with overlap. The capture plan must keep the reference visible in
   anchor frames for each measurement segment, or use multiple fixed targets with overlapping
   views. Room features used for a dimension must appear in enough overlapping frames to be
   associated with that metric frame.
4. Extract quality-controlled keyframes. Detect/match features, reject outliers with geometric
   verification, and estimate relative motion between adjacent frames.
5. Use `solvePnP` on visible metric-target corners to anchor camera poses where possible. For
   frames without the target, propagate pose only across verified overlap and record the
   resulting scale/pose uncertainty; do not silently treat unit translations as metric.
6. Triangulate repeated room landmarks from the calibrated projection matrices. Fit floor,
   wall, and ceiling planes only when enough valid points support each plane.
7. Compute room length, width, and height from documented plane intersections or visible corner
   landmarks. Mark unobserved or weakly supported dimensions pending.
8. Compare against independent tape-measure measurements and report errors and quality records.

This reference-assisted workflow is deliberately narrower than a full monocular SLAM system,
but it gives the assignment a defensible metric source. A known reference is not optional when
the moving-camera reconstruction does not independently recover scale.

### 6.2 Optional extension

A later extension may implement a fuller calibrated monocular SfM pipeline with global pose
refinement and scale constraints. It must not be started until the minimum viable workflow is
validated. Unit translation vectors from consecutive essential-matrix estimates cannot be
chained as though every camera motion had the same physical magnitude.

## 7. Web architecture

The future standalone provider will expose five pages:

1. Calibrated Stereo Object Measurement
2. Camera Calibration and Depth Visualization
3. Uncalibrated Stereo Handwritten Derivation
4. Video-Based Room Measurement
5. Results and Validation

Each page will display intermediate evidence, provenance, units, and honest pending states.
The page provider will satisfy the structural `get_pages()` contract used by the root dashboard,
but no dashboard or deployment repository will be edited in Phase 1.

## 8. Report-generation architecture

The final report has two synchronized deliverables:

```text
Module_7_Assignment_Report.docx  # editable primary source
Module_7_Assignment_Report.pdf   # submission-ready export of the DOCX
```

The planned source-of-truth structure is a report outline plus evidence manifest under
`docs/report/`, with real figures/results inserted only after Phases 2–6. The Word document is
the primary editable artifact. The PDF is produced from the Word document with a documented
conversion method and then visually inspected page by page. The scanned handwritten Q2 pages
must be embedded in both outputs; a typed derivation is not a substitute.

Phase 7 will verify heading numbering, table units, figure captions, equations, citations,
page breaks, hyperlinks, image resolution, embedded handwritten pages, and consistency between
the DOCX and PDF. Phase 1 does not generate a fake report or either final deliverable.

## 9. Git setup instructions for the user

These are manual instructions for a later authorized repository setup; they are not executed in
Phase 1:

```bash
cd /path/to/Assignments/Module_7
git init -b main
git remote add origin https://github.com/<your-account>/<module-7-repository>.git
git status
git branch --show-current
```

Before the first commit, decide which governance and assignment-source files remain local-only
using `.git/info/exclude`, mirror the established module policy, and confirm the exact public
repository URL. Development work should then use a task branch such as:

```bash
git switch -c task/module-7-phase-2-calibrated-stereo
```

The user must review the branch, staged paths, identity, and remote before any commit or push.
No root `Assignments/.git` should be created, and no other module's `.git` directory should be
copied.
