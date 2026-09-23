# Architecture

Module 3 is a standalone Python package using a `src/` layout.

## Core Package

- `module3.io_utils`: OpenCV image loading, upload decoding, grayscale conversion, and display
  conversion helpers.
- `module3.kernels`: normalized average and Gaussian kernel generation.
- `module3.spatial`: spatial filtering through OpenCV.
- `module3.fourier`: zero-padded Fourier-domain filtering.
- `module3.metrics`: MAE, MSE, RMSE, max error, and PSNR.
- `module3.comparison`: canonical spatial-vs-Fourier comparison pipeline.
- `module3.experiments`: reproducible experiment matrix and table serialization.
- `module3.visualization`: report figures and difference-image display helpers.

The core package does not import Streamlit.

## Web App

`app.py` is a thin Streamlit entry point. The web layer lives in `module3.webapp` and follows
the same page-provider shape as Module 2:

- `_page.py`: `PageSpec` contract.
- `registry.py`: provider-agnostic page collection.
- `shell.py`: sidebar navigation.
- `pages.py`: Module 3 page implementations.

This keeps Module 3 independently runnable while preserving a shape that a future course
dashboard could mount without importing Module 2 code.

## Reproducibility

`scripts/generate_sample_image.py` creates a deterministic input image. `scripts/run_experiments.py`
recomputes the result table and figures from that image. Automated tests use synthetic arrays and
do not depend on binary fixtures.
