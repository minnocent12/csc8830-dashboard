# Implementation Notes

## Spatial Path

The spatial path uses explicit normalized kernels and `cv2.filter2D`. OpenCV's `filter2D`
performs correlation rather than mathematical convolution, but the assignment kernels used here
are average and Gaussian kernels. Both are symmetric, so correlation and convolution are
identical after kernel flipping. Tests include an asymmetric-kernel example to document the
distinction.

The app also cross-checks the explicit-kernel path against `cv2.blur` and `cv2.GaussianBlur`
in tests. The explicit-kernel `filter2D` path is the canonical path for comparison because it
makes the kernel values visible and reusable by the Fourier implementation.

## Fourier Path

For an image with shape `M x N` and an odd kernel with shape `Kh x Kw`, the implementation:

1. Converts the grayscale image to `float64`.
2. Pads the image by `Kh // 2` rows and `Kw // 2` columns on all sides with zeros.
3. Places the kernel into a zero array with the same padded shape.
4. Rolls the kernel by `(-Kh // 2, -Kw // 2)` so the kernel center is at array index `(0, 0)`.
5. Computes `fft2(image_pad) * fft2(kernel_pad)`.
6. Applies `ifft2`.
7. Keeps the real component after recording the maximum imaginary component.
8. Crops the original `M x N` region.

This computes linear convolution over the original image region rather than accidental circular
convolution.

## Boundary Handling

The numerical comparison uses `cv2.BORDER_CONSTANT` in the spatial path and the same zero
assumption in the Fourier path. This is required for a fair comparison. If the spatial path used
OpenCV's reflective default while the Fourier path used zero padding, the difference image and
MAE/MSE would measure boundary mismatch rather than the convolution theorem.

The "Filtering Demo" web page uses `BORDER_REFLECT_101` for display because it avoids dark
edges on uploaded photos. That preview is not used for the MAE/MSE validation table.

## Precision

All comparison computations use `float64`. The code clips and rounds to `uint8` only for display
or image saving. Metrics are computed before any display conversion.

## Color Handling

The theoretical and experimental comparison uses single-channel grayscale images because the
assignment formulas describe a scalar image `f[x, y]`. The filtering demo applies the same kernel
independently to each BGR channel for a natural preview. No cross-channel filtering is performed.

## Validation Status

- Implemented: kernel generation, spatial filtering, Fourier filtering, comparison metrics,
  scripts, figures, Streamlit pages, and documentation.
- Tested: deterministic unit tests cover kernels, I/O, spatial filtering, Fourier alignment,
  metrics, experiments, and web page registration.
- Experimentally validated: `scripts/run_experiments.py` generated the MAE/MSE table in
  `results/experiment_results.md` on the deterministic sample image.
- Pending user submission work: final PDF assembly, GitHub repository publication/access, and
  demonstration video recording.
