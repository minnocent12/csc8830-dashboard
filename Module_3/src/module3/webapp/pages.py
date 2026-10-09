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
from module3.webapp.design.components import (
    equation_block,
    page_header as kit_page_header,
    theory_section,
)
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
    st.warning(
        "No image uploaded and the bundled sample image is not available. Upload an image to "
        "continue."
    )
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
    kit_page_header(
        "Theory",
        eyebrow=_MODULE,
        description="Written derivation of the convolution theorem for the Module 3 image filtering implementation.",
    )

    doc = _DOCS_DIR / "CONVOLUTION_THEOREM.md"
    if not doc.is_file():
        st.error("The convolution theorem derivation is not available.")
        return

    st.caption("Written derivation of the convolution theorem.")

    with theory_section("Variables"):
        st.markdown(
            "- `f[x, y]`: grayscale input image intensity at pixel coordinate `(x, y)`.\n"
            "- `h[m, n]`: spatial-domain blur kernel at kernel coordinate `(m, n)`.\n"
            "- `g[x, y]`: filtered image.\n"
            "- `*`: discrete 2D convolution.\n"
            "- `F[u, v]`: 2D discrete Fourier transform (DFT) of `f[x, y]`.\n"
            "- `H[u, v]`: 2D DFT of `h[m, n]`.\n"
            "- `G[u, v]`: 2D DFT of `g[x, y]`."
        )

    with theory_section("Derivation"):
        st.markdown("The spatial-domain filtering operation is")
        equation_block(
            r"g[x, y] = (f * h)[x, y] = \sum_m \sum_n f[x-m,\, y-n]\, h[m, n]",
        )
        st.markdown("The 2D DFT of `g` is")
        equation_block(
            r"G[u, v] = \sum_x \sum_y g[x, y]\, \exp\!\left(-j\,2\pi"
            r" \left(\frac{ux}{M} + \frac{vy}{N}\right)\right)",
        )
        st.markdown("Substitute the convolution definition:")
        equation_block(
            r"G[u, v] = \sum_x \sum_y \sum_m \sum_n"
            r" f[x-m,\, y-n]\, h[m, n]\, \exp\!\left(-j\,2\pi"
            r" \left(\frac{ux}{M} + \frac{vy}{N}\right)\right)",
        )
        st.markdown("Let `a = x - m` and `b = y - n`, so `x = a + m` and `y = b + n`:")
        equation_block(
            r"G[u, v] = \sum_m \sum_n h[m, n] \sum_a \sum_b f[a, b]\, \exp\!\left(-j\,2\pi"
            r" \left(\frac{u(a+m)}{M} + \frac{v(b+n)}{N}\right)\right)",
        )
        st.markdown("Split the exponential into an image-coordinate factor and a kernel-coordinate factor:")
        equation_block(
            r"G[u, v] = \sum_m \sum_n h[m, n]\, \exp\!\left(-j\,2\pi"
            r" \left(\frac{um}{M} + \frac{vn}{N}\right)\right)"
            r" \sum_a \sum_b f[a, b]\, \exp\!\left(-j\,2\pi"
            r" \left(\frac{ua}{M} + \frac{vb}{N}\right)\right)",
        )
        st.markdown(
            "The second sum is the DFT of the image, `F[u, v]`. "
            "The first sum is the DFT of the kernel, `H[u, v]`. Therefore:"
        )
        equation_block(r"G[u, v] = H[u, v]\, F[u, v]")
        st.markdown("So:")
        equation_block(r"\text{DFT}\{f * h\} = \text{DFT}\{f\}\, \text{DFT}\{h\}")
        st.markdown("and the equivalent filtering result can be recovered with the inverse transform:")
        equation_block(r"f * h = \text{IDFT}\!\left(F[u, v]\, H[u, v]\right)")

    with theory_section("Connection to the Implementation"):
        st.markdown(
            "The theorem above describes convolution on a domain where the shifted values are "
            "well-defined. An FFT computes circular convolution unless the arrays are padded. "
            "This project zero-pads the image by the kernel radius on all sides, embeds the "
            "kernel into the same padded shape, rolls the kernel so its center is at the DFT "
            "origin, multiplies the spectra, applies the inverse FFT, and crops the original "
            "image region. That recipe makes the Fourier-domain result match the zero-boundary "
            "spatial convolution used by `cv2.filter2D`."
        )


def get_pages() -> list[PageSpec]:
    """Return the Module 3 pages contributed to a Streamlit host."""
    return [
        PageSpec(_MODULE, "Image Blurring", 10, _filtering_demo_page),
        PageSpec(_MODULE, "Spatial vs Fourier", 20, _comparison_page),
        PageSpec(_MODULE, "Experimental Validation", 30, _experimental_validation_page),
        PageSpec(_MODULE, "Theory", 40, _theory_page),
    ]
