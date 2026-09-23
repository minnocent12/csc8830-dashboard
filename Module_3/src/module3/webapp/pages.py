"""Module 3 Streamlit pages and the ``get_pages`` provider."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import streamlit as st

from module3.comparison import compare_spatial_fourier
from module3.io_utils import bgr_to_gray_float64, decode_image_bgr, load_image_bgr
from module3.kernels import KernelSpec, make_kernel
from module3.spatial import apply_filter2d_bgr
from module3.visualization import contrast_stretch
from module3.webapp._page import PageSpec
from module3.webapp.ui import IMAGE_TYPES, results_missing_notice, show_bgr_image, show_gray_image

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOCS_DIR = _REPO_ROOT / "docs"
_RESULTS_DIR = _REPO_ROOT / "results"
_SAMPLE_IMAGE = _REPO_ROOT / "data" / "sample_images" / "module3_sample.png"
_MODULE = "Module 3"


def _load_user_or_sample_image(label: str) -> tuple[np.ndarray | None, str]:
    upload = st.file_uploader(label, type=IMAGE_TYPES)
    if upload is not None:
        return decode_image_bgr(upload.getvalue()), upload.name
    if _SAMPLE_IMAGE.is_file():
        return load_image_bgr(_SAMPLE_IMAGE), _SAMPLE_IMAGE.name
    st.warning("No uploaded image and no bundled sample image found.")
    st.code("python scripts/generate_sample_image.py")
    return None, ""


def _kernel_controls(prefix: str) -> KernelSpec:
    c1, c2 = st.columns(2)
    filter_name = c1.selectbox("Filter", ["Average Blur", "Gaussian Blur"], key=f"{prefix}_filter")
    size = int(c2.select_slider("Kernel size", options=[3, 5, 7, 9, 11], value=5, key=f"{prefix}_size"))
    key = "average" if filter_name == "Average Blur" else "gaussian"
    return make_kernel(key, size)


def _show_kernel(kernel_spec: KernelSpec) -> None:
    st.caption(f"{kernel_spec.filter_name} {kernel_spec.size}x{kernel_spec.size}; values sum to {kernel_spec.kernel.sum():.6f}.")
    st.dataframe(np.round(kernel_spec.kernel, 6), width="stretch")


def _filtering_demo_page() -> None:
    st.header("Image Blurring")
    image, image_name = _load_user_or_sample_image("Image")
    if image is None:
        return
    kernel_spec = _kernel_controls("demo")
    _show_kernel(kernel_spec)

    filtered = apply_filter2d_bgr(image, kernel_spec.kernel, border_type=cv2.BORDER_REFLECT_101)
    st.caption(
        "Display preview uses per-channel BGR filtering with BORDER_REFLECT_101. "
        "The numerical comparison pages use grayscale with matched zero boundaries."
    )
    c1, c2 = st.columns(2)
    with c1:
        show_bgr_image(image, caption=f"Original: {image_name}")
    with c2:
        show_bgr_image(filtered, caption=f"{kernel_spec.filter_name} {kernel_spec.size}x{kernel_spec.size}")


def _comparison_page() -> None:
    st.header("Spatial vs Fourier")
    image, image_name = _load_user_or_sample_image("Image for comparison")
    if image is None:
        return
    kernel_spec = _kernel_controls("comparison")
    gray = bgr_to_gray_float64(image)
    result = compare_spatial_fourier(gray, kernel_spec.kernel)

    st.caption(
        "Comparison uses grayscale float64 data and matched zero boundary conditions in both "
        "paths so the measured errors test the convolution theorem rather than edge-policy differences."
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        show_gray_image(result.original, caption=f"Original grayscale: {image_name}")
    with c2:
        show_gray_image(result.spatial, caption="Spatial result")
    with c3:
        show_gray_image(result.fourier, caption="Fourier result")
    with c4:
        st.image(
            contrast_stretch(result.difference),
            caption="Difference, contrast-stretched",
            width="stretch",
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("MAE", f"{result.metrics.mae:.3e}")
    m2.metric("MSE", f"{result.metrics.mse:.3e}")
    m3.metric("RMSE", f"{result.metrics.rmse:.3e}")
    m4.metric("Max error", f"{result.metrics.max_abs_error:.3e}")
    psnr = "inf" if np.isinf(result.metrics.psnr_db) else f"{result.metrics.psnr_db:.2f}"
    m5.metric("PSNR (dB)", psnr)
    st.caption(f"Max discarded imaginary component after inverse FFT: {result.max_imaginary_abs:.3e}.")


def _experimental_validation_page() -> None:
    st.header("Experimental Validation")
    results_doc = _RESULTS_DIR / "experiment_results.md"
    if not results_doc.is_file():
        results_missing_notice()
        return
    st.markdown(results_doc.read_text(encoding="utf-8"))
    csv_path = _RESULTS_DIR / "experiment_results.csv"
    if csv_path.is_file():
        st.download_button(
            "Download CSV",
            data=csv_path.read_text(encoding="utf-8"),
            file_name="experiment_results.csv",
            mime="text/csv",
        )


def _theory_page() -> None:
    st.header("Theory")
    doc = _DOCS_DIR / "CONVOLUTION_THEOREM.md"
    if not doc.is_file():
        st.error(f"Theory document not found: {doc}")
        return
    st.caption(f"Source: `docs/{doc.name}`")
    st.markdown(doc.read_text(encoding="utf-8"))


def get_pages() -> list[PageSpec]:
    """Return the Module 3 pages contributed to a Streamlit host."""
    return [
        PageSpec(_MODULE, "Image Blurring", 10, _filtering_demo_page),
        PageSpec(_MODULE, "Spatial vs Fourier", 20, _comparison_page),
        PageSpec(_MODULE, "Experimental Validation", 30, _experimental_validation_page),
        PageSpec(_MODULE, "Theory", 40, _theory_page),
    ]
