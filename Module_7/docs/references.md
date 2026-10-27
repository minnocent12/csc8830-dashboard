# Module 7 Reference Ledger

All references used in the final assignment reports must be cited in the relevant prose,
equation, figure caption, table note, or algorithm description. This ledger is a Phase 1
starting point; it is not a claim that the final report bibliography is complete.

## Verified references

### [OpenCV-Calib]

OpenCV. “Camera Calibration.” *OpenCV-Python Tutorials*, OpenCV 4.x. Official documentation:
<https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html>. Accessed 2026-10-23.

Planned uses: distortion model, intrinsic calibration, target corner refinement, calibration
workflow, and undistortion discussion in the Q1 method and calibration protocol.

### [OpenCV-Calib3d]

OpenCV. “Camera Calibration and 3D Reconstruction.” *OpenCV 4.x `calib3d` Reference*.
<https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html>. Accessed 2026-10-23.

Planned uses: essential/fundamental geometry APIs, `recoverPose`, stereo rectification,
`triangulatePoints`, `reprojectImageTo3D`, projection conventions, and documented API behavior.

### [Hartley-Zisserman]

Hartley, Richard, and Andrew Zisserman. *Multiple View Geometry in Computer Vision*. 2nd ed.,
Cambridge University Press, 2004. Oxford Visual Geometry Group reference page:
<https://robots.ox.ac.uk/~vgg/hzbook/index.html>. Publisher DOI:
<https://doi.org/10.1017/CBO9780511811685>. Accessed 2026-10-23.

Planned uses: projective camera models, epipolar geometry, fundamental matrix, triangulation,
projective reconstruction, and metric/projective ambiguity in Q2 and Q3.

## Citation-use map

| Report topic | Required citation(s) | Evidence/source to cite alongside it |
| --- | --- | --- |
| Smartphone calibration and distortion | [OpenCV-Calib] | Actual calibration protocol and user data manifest |
| Relative pose and rectification | [OpenCV-Calib3d], [Hartley-Zisserman] | Actual pose/rectification outputs |
| `Z=fB/d` assumptions | [OpenCV-Calib3d], [Hartley-Zisserman] | Derivation and rectified-pair evidence |
| Triangulation and 3D points | [OpenCV-Calib3d], [Hartley-Zisserman] | Actual correspondence and reprojection records |
| Uncalibrated stereo derivation | [Hartley-Zisserman] | Student's handwritten pages and page references |
| Moving-camera multiview geometry | [Hartley-Zisserman], [OpenCV-Calib3d] | Actual video/keyframe/pose records |
| Public dataset or reference image, if used | Dataset's authoritative license/source | Exact committed file and provenance |
| Any additional algorithm or research claim | Verify and add a source before use | Section/figure/table where used |

## Citation rules for later phases

- Do not cite a search-result page when the authoritative document is available.
- Do not invent authors, publication dates, DOI values, dataset licenses, or access dates.
- Cite the source of a method separately from the project's own implementation decisions.
- Label equations derived by the student versus equations adopted from a source.
- Cite any external figure directly in its caption and record permission/license information.
- Record the exact OpenCV version and any API behavior that materially affects results.
