# Phase 3C Polygon Edge-Length Validation Protocol

## Scope and current gate

This protocol prepares, but does not process, a real polygon experiment. Polygon validation is
authorized; Phase 4 and dashboard/report work remain out of scope. The preferred first object is a
rigid, flat triangle because it has only three vertices and three visible edges. A pentagon is also
acceptable if all five corners remain unobstructed.

The yellow-lid circle experiment is closed as:

`EXPERIMENT DOCUMENTED — PHYSICAL REFERENCE ESTABLISHED; STEREO CIRCLE GEOMETRY REJECTED`.

Its calibration, correspondences, thresholds, and rejection evidence are unchanged.

## Object and measurement preparation

1. Select a rigid, flat, opaque triangular card, sheet, panel, or plate with three sharp, visible
   corners. Avoid flexible paper, rounded corners, reflective surfaces, transparent material, and
   partly hidden vertices.
2. Use a contrasting background. If needed, place small removable marks along the edges near each
   vertex to preserve identity, but do not cover or move the actual corner. The measured endpoint is
   the physical corner itself, not the center of a nearby mark.
3. Label the corners physically and in a sketch. For a triangle, use a consistent clockwise order:
   `v0`, `v1`, `v2`. For a pentagon use `v0` through `v4`. The closing edge is included automatically
   by the closed-polygon measurement path.
4. Measure every visible straight edge independently before stereo processing. Take at least three
   ruler/tape readings per edge, record every reading in millimetres, calculate the mean, and record
   the ruler resolution and a defensible uncertainty. Do not assume ±1 mm unless the actual ruler
   resolution, endpoint alignment, perspective, and repeated readings support it.
5. Photograph each physical measurement with the scale units, zero/reference mark, and both exact
   corner endpoints visible. These photographs establish physical reference evidence only; they must
   not be used to rescale or optimize the stereo reconstruction.

## Scene and phone setup

1. Place the polygon flat and rigid on a stable support. Place the existing 9×6 checkerboard with
   25 mm squares stationary and fully visible in the same scene, preferably on the same support plane
   and close enough to the polygon for reliable detection without hiding any vertex.
2. Mark the support positions of both the polygon and checkerboard. Nothing except the phone may move
   between the two stereo views.
3. Use the calibrated iPhone 15 Pro Max with the same calibrated lens/camera mode, resolution,
   orientation, focus, exposure, and zoom. Do not enable digital zoom or change camera mode between
   views. Lock focus on the scene if the camera app permits it.
4. Capture view 1 with the entire checkerboard and polygon sharp and unobstructed. Move the phone
   laterally, approximately 80–120 mm as a starting target, then capture view 2 with similar height,
   nearly unchanged orientation, substantial overlap, and no motion blur. This displacement is a
   practical target, not a substitute for the recovered checkerboard-PnP baseline. The metric camera
   translation will be recovered from the 25 mm checkerboard geometry.
5. Keep enough lateral viewpoint difference to produce visible polygon parallax, but do not rotate or
   translate so far that the checkerboard, a vertex, or an edge leaves the frame. Record the capture
   order and any physical phone displacement measurement if available.
6. Preserve the original full-resolution files without editing. Suggested names are
   `data/physical_validation/phase3c_polygon_view1.JPG` and
   `data/physical_validation/phase3c_polygon_view2.JPG`.

## Capture checklist

- [ ] Rigid, flat triangle or pentagon selected; all vertices and edges visible.
- [ ] Physical corner labels/sketch completed in clockwise order.
- [ ] Three independent readings recorded for every visible edge.
- [ ] Ruler resolution, uncertainty rationale, and measurement photographs recorded.
- [ ] Checkerboard is stationary, fully visible, and not occluding the polygon.
- [ ] Polygon and checkerboard support positions marked.
- [ ] Phone settings match the validated calibration; focus and zoom remain fixed.
- [ ] View 1 and view 2 are sharp, full resolution, overlapping, and laterally displaced.
- [ ] Original filenames and capture order preserved.

## Processing gate after the user supplies images

No correspondence coordinates are selected before the originals are inspected. The existing workflow
will first run checkerboard-PnP and metric triangulation:

```bash
python scripts/process_stereo_pair.py \
  --calibration results/calibration/module2_originals_module7_recomputed.json \
  --view1 data/physical_validation/phase3c_polygon_view1.JPG \
  --view2 data/physical_validation/phase3c_polygon_view2.JPG \
  --pose-method checkerboard_pnp \
  --auto-correspondences-output results/object_measurements/polygon_phase3c/checkerboard_correspondences.csv \
  --output results/object_measurements/polygon_phase3c/checkerboard_stereo.json \
  --diagnostic-image results/stereo_diagnostics/polygon_phase3c/checkerboard_correspondences.png
```

After visual verification, record the same physical vertices in both portrait-coordinate images in
the existing `point_id,u1,v1,u2,v2` CSV format. Use `v0,v1,v2` (or `v0`–`v4`) in clockwise order.
The point coordinates must be selected from the actual corners, not guessed from a bounding box.
Then run the existing object-measurement CLI with `--shape polygon`; use `--require-planar` for the
flat-object experiment only after the reconstructed planarity diagnostics are reviewed. The workflow
must report positive depth, parallax, reprojection errors, planarity, reconstructed vertices, and each
adjacent Euclidean edge length before any physical comparison is made.

The resulting edge means are compared independently with the ruler means. Signed error, absolute error,
percentage error, uncertainty intervals, and limitations are recorded only from the supplied physical
measurements. A passing geometry gate is not by itself a physical-accuracy pass.
