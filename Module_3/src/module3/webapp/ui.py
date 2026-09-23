"""Small Streamlit helpers used by the Module 3 pages."""
from __future__ import annotations

import cv2
import numpy as np
import streamlit as st

from module3.io_utils import to_display_uint8

IMAGE_TYPES = ["jpg", "jpeg", "png", "bmp", "tif", "tiff"]


def results_missing_notice() -> None:
    """Show the standard notice for generated experiment results."""
    st.warning(
        "Results have not been generated yet. Run `python scripts/generate_sample_image.py` "
        "and `python scripts/run_experiments.py` from the Module_3 repository root."
    )


def show_gray_image(image: np.ndarray, *, caption: str) -> None:
    """Render a grayscale image after display-only clipping."""
    st.image(to_display_uint8(image), caption=caption, clamp=True, width="stretch")


def show_bgr_image(image_bgr: np.ndarray, *, caption: str) -> None:
    """Render a BGR image in Streamlit's RGB expectation."""
    rgb = cv2.cvtColor(to_display_uint8(image_bgr), cv2.COLOR_BGR2RGB)
    st.image(rgb, caption=caption, clamp=True, width="stretch")
