# Phase 3A — Rectangle Physical Validation Protocol

**Status:** `CAPTURED — RECONSTRUCTED; PROVISIONAL PHYSICAL INTERVALS FAIL; VALIDATION NOT COMPLETE`

This protocol is for the rectangle experiment only. Circle and polygon validation are outside
the current authorization.

## Validated inputs to reuse

- Camera: the calibrated Apple iPhone 15 Pro Max lens recorded in Module 2 EXIF evidence
  (6.765 mm physical focal length, 24 mm 35-mm equivalent, f/1.78).
- Calibration ID: `module2-originals-module7-recompute`.
- Calibration frame: `(4284, 5712)` pixels in the portrait coordinate convention.
- Calibration target: 9×6 internal corners, 25.0 mm physical square size.
- Calibration record:
  `results/calibration/module2_originals_module7_recomputed.json`.
- Pose method: `checkerboard_pnp`, using the same stationary checkerboard in both views.

The original phone files must remain unchanged. If OpenCV decodes the new iPhone files as
`(5712, 4284)`, derived 90-degree clockwise portrait copies will be created for processing,
while the originals remain in their supplied location. For this experiment the originals are
`data/physical_validation/IMG_7514.JPG` and `IMG_7515.JPG`.

## Physical setup

1. Use a rigid, flat rectangular reference with four sharp, clearly visible outer corners. A
   stiff card, thin board, or box face is suitable; avoid soft, bent, rounded, or occluded edges.
2. Mark the four corners only if the marks do not change the physical endpoints being measured.
   The intended order is `top_left`, `top_right`, `bottom_right`, `bottom_left` as viewed in
   the first image.
3. Measure the physical top edge from the same two outer corner points selected as
   `top_left`–`top_right`. Measure the physical left edge from `top_left`–`bottom_left`.
   Record three readings for each dimension, the mean, units, and ruler/tape uncertainty.
4. Mount or place the checkerboard so it cannot move. Keep the complete 9×6 inner-corner
   pattern visible in both views and do not let the rectangle hide it.
5. Keep the rectangle stationary between captures. Place it close enough to be sharp and large
   enough that each corner is unambiguous, while keeping the checkerboard visible with useful
   image area and overlap.

## Phone settings and capture

1. Use the same iPhone 15 Pro Max main lens/camera mode used for the validated calibration.
   Use 1×/24-mm-equivalent framing, no digital or optical zoom change, and the same portrait
   orientation convention. Do not switch to ultrawide, telephoto, macro, or cinematic mode.
2. Keep resolution, lens, focus behavior, exposure behavior, and aspect ratio fixed. Lock focus
   and exposure if the camera application permits it; otherwise tap the stationary target and
   avoid changing lighting or focus distance between views.
3. Capture `rectangle_view1.JPG` from the first position. Move the phone laterally by a useful
   amount comparable to the validated experiment, approximately 8–12 cm as a capture target,
   without treating the phone body displacement as an exact camera-center baseline.
4. Keep the object and checkerboard stationary. Maintain substantial overlap and broadly similar
   orientation; do not rotate the phone enough to lose the board or rectangle. A small viewpoint
   change is useful, but motion blur, rolling-shutter motion, or a large out-of-plane rotation
   can make correspondences unreliable.
5. Capture `rectangle_view2.JPG` from the second position. Do not crop, resize, rotate, enhance,
   or overwrite either original file.

The planned storage location for future rectangle captures is:

```text
data/objects/rectangle/rectangle_view1.JPG
data/objects/rectangle/rectangle_view2.JPG
```

## Processing gates after capture

The next interaction begins only after the originals and physical measurement record are
available. The processing sequence will be:

1. Inspect both originals for dimensions, focus, blur, checkerboard visibility, rectangle
   visibility, overlap, and unchanged camera settings.
2. Create only derived portrait-coordinate copies if required by the calibrated frame.
3. Verify the four corner correspondences visually in both images and record the CSV in the
   order `top_left,top_right,bottom_right,bottom_left` using the processed image coordinates.
4. Run `scripts/process_stereo_pair.py --pose-method checkerboard_pnp` with the existing
   calibration, both processed views, and the rectangle correspondence CSV.
5. Run `scripts/measure_object.py --shape rectangle` using the saved stereo record. The script
   must recover all four metric 3D points before calculating width and height.
6. Review checkerboard-PnP reprojection, object-point positive depth, parallax, object-point
   reprojection error, rectangle coplanarity, opposite-edge disagreement, and right-angle
   diagnostics.
7. Compare reconstructed width and height with the independent physical means and uncertainty
   intervals. Report signed error, absolute error, and percentage error without rescaling the
   reconstruction. No physical pass will be claimed until the real evidence is reviewed.

The software quality defaults are diagnostics, not claims of physical accuracy: maximum point
reprojection error 5 px, minimum median parallax 0.01 degrees, opposite-edge disagreement 5%,
planarity residual 5% of the larger dimension, and right-angle deviation 15 degrees.

## Current supplied experiment record

The supplied images were processed without modifying the originals. `IMG_7514.JPG` required a
90-degree clockwise derived portrait-frame conversion; `IMG_7515.JPG` was already portrait-sized
after OpenCV decoding. The existing 9×6 checkerboard was detected in both views and
checkerboard-PnP produced a 44.6969976 mm metric baseline. Four reviewed card boundary
correspondences passed positive-depth and 5 px reprojection checks. The saved reconstruction is
51.4434472 mm for the image-order top edge and 85.8989759 mm for the image-order side edge.

The user supplied repeated means of 49.40 mm for the shorter card dimension and 87.40 mm for the
longer dimension. The 1 mm ruler subdivisions and repeated-reading spread support a provisional
±1.0 mm physical bound, giving intervals 48.40–50.40 mm and 86.40–88.40 mm. The reconstructed
short edge is 51.4434472 mm, 1.0434472 mm above its interval; the reconstructed long edge is
85.8989759 mm, 0.5010241 mm below its interval. Both provisional intervals fail. This bound is
not stereo-system uncertainty, no percentage-error threshold was introduced, and endpoint/setup
photographs for this rectangle are not available. The experiment remains `PHYSICAL VALIDATION
NOT COMPLETE`; see the evidence manifest and validation JSON under `results/`.

## Second supplied experiment

`IMG_7516.JPG` and `IMG_7517.JPG` were preserved and processed with the same calibration,
checkerboard-PnP method, correspondence ordering, and quality thresholds. Both detected 54/54
checkerboard corners. The recovered baseline was 6.0410615 mm and median card parallax was
0.669038 degrees. Although all four landmarks passed positive-depth and point-reprojection
checks, the rectangle gate rejected the geometry because opposite-edge disagreement was 24.1595%
for width and 17.8049% for height; planarity RMS/max were 5.08290 / 5.95519 mm and maximum
right-angle deviation was 21.9274 degrees. No accepted dimensions were produced.

The supplied ruler photographs `IMG_7501.JPG` and `IMG_7502.JPG` were re-inspected and show the
FREE ADMISSION card. `IMG_7501.JPG` places the ruler along the long horizontal front-face edge;
`IMG_7502.JPG` places it along the short edge. The zero reference, millimetre subdivisions, and
both endpoints are visible sufficiently to support the repeated readings 87.0/88.0/87.2 mm and
49.0/49.8/49.4 mm. The means remain 87.40 mm and 49.40 mm. A conservative ±1.00 mm uncertainty
is supported by the 1 mm subdivisions, endpoint alignment, perspective, and reading spread; this
is not stereo-system uncertainty. The measurements were not used to rescale or optimize any stereo
result.

## Third experiment gate and result

The previously blocked third experiment was resumed after the untouched originals were supplied as
`data/physical_validation/IMG_7519.JPG` and `data/physical_validation/IMG_7520.JPG`. Both originals
were preserved. They are Apple iPhone 15 Pro Max files at 4284×5712 decoded resolution with EXIF
orientation 6; OpenCV decoded the portrait arrays directly in the calibrated frame, so no content
rotation was applied.

The existing checkerboard-PnP workflow detected 54/54 internal corners in each view. PnP RMS
reprojection errors were 1.10839 px and 2.21646 px, the metric baseline was 166.387025 mm, and
median card parallax was 17.073946 degrees. Four card corners were independently recorded in the
required order. All four points passed positive-depth, point-reprojection, planarity, right-angle,
and opposite-edge checks. The reconstructed short and long dimensions were 52.336899 mm and
92.973060 mm. Compared with 49.40 mm and 87.40 mm, the signed errors were +2.936899 mm and
+5.573060 mm; both are outside the provisional ±1.00 mm intervals.

The experiment is nevertheless `DOCUMENTED — FREE ADMISSION MEASUREMENT VERIFIED; STEREO ACCURACY
NOT VALIDATED`. The checkerboard homography residual median/max were 3.891/8.593 px,
whereas card-corner residuals were 14.937–46.805 px. This is objective evidence that the
card-to-board relationship is not sufficient to establish a stationary common scene. This residual
screen is decisive only if the card and checkerboard are coplanar; the calibrated card-homography
decomposition was also reviewed. The previously reported 12.345324-degree discrepancy used raw
distorted pixels; distortion-aware point normalization gave a closest discrepancy of 12.959758
degrees. With only four card corners and no independently known card-plane geometry, this is a
pose/model warning, not an independent pose estimate or proof of card movement. The selected points
visually refer to the same apparent outer corners in both views, and the horizontal image-order edge
is the short side while the vertical edge is the long side. The verified ruler evidence supports
both physical means and the conservative ±1.00 mm intervals, but both reconstructed dimensions
remain outside those intervals. This is a legitimate experimental accuracy limitation. The prior
blocked-missing-originals audit record remains preserved; no calibration, threshold, scale,
correspondence, or accepted point was changed to obtain agreement. No recapture is requested
automatically.
