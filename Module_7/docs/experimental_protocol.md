# Module 7 Experimental Protocol — Objects and Room Video

**Status:** Phase 3 software implementation complete and tested. Phase 3A rectangle capture and
stereo reconstruction are complete; physical measurements are verified but both stereo dimensions
remain outside their reference intervals. Phase 3B marked yellow-lid capture has valid checkerboard-
PnP and point-level stereo results, but the recovered rim fails the existing 3D planarity gate. Lid
photos now document a provisional 100.0 ± 2.0 mm physical outer-rim reference; this does not repair or
validate the rejected stereo result. Polygon validation remains unauthorized.
See `docs/rectangle_validation_protocol.md` for the controlled capture gate.

## 1. Evidence and provenance rules

Every real result must be traceable to:

- a calibration ID;
- source image/video filenames and frame indices;
- the camera configuration and image dimensions;
- the baseline or metric reference used;
- landmark/correspondence records;
- independent physical measurements;
- the script/configuration used to produce the derived result.

Raw personal captures remain private unless the user explicitly chooses to publish them. Small
derived evidence may be committed only after confirming it is real, permissible to publish, and
tracked by the Module 7 repository.

## 2. Question 1 object validation

### 2.1 Capture plan

For each object trial:

1. select a stationary object and record its shape;
2. measure the ground-truth dimensions independently with a ruler or measuring tape;
3. record the measurement unit and uncertainty/precision of that physical measurement;
4. capture the sequential stereo pair using the calibration protocol;
5. record the measured camera-center displacement and any support/position marks;
6. identify visible landmarks in boundary order;
7. retain the original images and a provenance manifest;
8. process only after the capture metadata is complete.

Manual landmark selection is the first implementation path. Automatic feature matching may
propose candidates, but the final correspondence table must identify which points were accepted
and why.

### 2.2 Shape-specific records

- **Rectangle:** record four visible corners in clockwise or counterclockwise order. Report
  adjacent 3D edge lengths for the requested observable dimensions.
- **Circle:** record the planar-object assumption, the number/source of perimeter landmarks,
  the fitted plane/circle method, and the recovered diameter. If the boundary is occluded or
  the planar/circular assumptions fail, mark diameter pending.
- **Polygon:** record all visible vertices in boundary order and calculate every adjacent edge
  length. Do not silently substitute a bounding-box width/height.

### 2.3 Measurement table

The future result table must contain, at minimum:

| Field | Unit/status |
| --- | --- |
| object identifier and shape | categorical |
| calibration ID and stereo ID | provenance |
| left/right image IDs | provenance |
| baseline and pose evidence | m or mm; measured/estimated |
| reconstructed landmark coordinates | m or mm |
| reconstructed depth `Z` | m or mm |
| estimated dimension | m or mm |
| independent physical dimension | m or mm; user-measured |
| absolute error | same unit |
| percentage error | percent |
| quality notes | text |

For a dimension `a` and estimate `â`, calculate:

```text
absolute_error = |â - a|
percentage_error = 100 * |â - a| / |a|, for a != 0
```

The implementation may also retain signed error `â - a` for analysis. Statistics are reported
only after real observations exist; synthetic tests are labeled software tests.

## 3. Question 3 moving-camera room video

### 3.1 Minimum viable reference-assisted capture

The initial Q3 scope is a calibrated, single-smartphone, moving-camera video with a physical
metric reference. It is not an unrestricted monocular room scanner.

The user must provide:

- the calibrated phone and exact video resolution/lens mode;
- a fixed, measured reference target or known-length geometry;
- a room with visible floor/wall/ceiling boundaries and sufficient texture;
- an independent tape-measure record of length, width, and height where physically accessible.

The reference target should be fixed in the room and visible in anchor frames for each
measurement segment. If the room cannot be covered while keeping one reference visible, use
multiple fixed measured targets with overlapping segments and document their common coordinate
frame. A segment with no metric connection to the reference remains unscaled and cannot support
an absolute dimension claim.

### 3.2 Video path

1. Start with the reference target and the room features needed for the first measurement in
   view; record an anchor segment.
2. Move the phone slowly through a path with overlap and adequate parallax. Avoid rapid panning,
   motion blur, autofocus changes, and featureless walls.
3. Record room corners, floor/wall intersections, wall/ceiling intersections, and any occlusion
   or unobserved region in the capture notes.
4. Extract frames with timestamps and quality metadata. Do not treat every frame as an
   independent measurement without checking blur and pose consistency.
5. Select keyframes, detect/match features, verify geometric inliers, estimate relative pose,
   and triangulate only points with sufficient support.
6. Use visible metric-target corners with `solvePnP` to anchor camera poses where possible. For
   target-free frames, propagate only through verified overlap and retain uncertainty; unit
   translations from `recoverPose` are not metric by themselves.
7. Fit floor, wall, and ceiling planes when enough reconstructed points support them. Estimate
   dimensions from documented plane intersections or room-corner landmarks.
8. Compare estimates with independent physical measurements.

### 3.3 Coverage acceptance

A dimension may be reported only when:

- the relevant room boundaries are visible or geometrically supported;
- the reconstruction segment is connected to the metric reference;
- sufficient parallax and inliers are present;
- plane/corner residuals are recorded;
- the physical validation measurement exists or the result is clearly labeled not validated.

Otherwise report `PENDING USER EXPERIMENT`, `NOT MEASURED`, or `NOT VALIDATED` as appropriate.

### 3.4 Room result table

| Field | Unit/status |
| --- | --- |
| room/video/reference identifiers | provenance |
| selected frame IDs and timestamps | provenance |
| valid feature/inlier counts | computed evidence |
| reference scale source | measured reference |
| floor/wall/ceiling plane parameters | room-frame coordinates |
| estimated length, width, height | m or mm |
| actual length, width, height | user-measured |
| absolute and percentage errors | m/mm and percent |
| plane residual/reprojection/coverage indicators | computed evidence |
| failure/occlusion/unknown-region notes | text |

## 4. Failure modes

The application must expose rather than conceal:

- insufficient feature texture;
- repeated or ambiguous features;
- motion blur or rolling-shutter effects;
- too little camera motion/parallax;
- camera pose ambiguity or cheirality failure;
- reference target absent or not metric;
- disconnected reconstruction segments;
- occluded or unobserved room boundaries;
- plane-fit residuals too large for the documented tolerance;
- missing independent physical validation.

No failure mode is repaired by inserting a plausible dimension.
