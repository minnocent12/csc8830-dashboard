"""Question 1 evidence pages backed by saved Module 7 artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from module7.webapp._page import PageSpec
from module7.webapp.evidence import load_curated_bundle
from module7.webapp.ui import (
    metric_row,
    page_header,
    render_3d_table,
    render_bundled_notice,
    render_bundle_summary,
    render_diagnostics,
    render_image_pair,
    render_limitations,
    render_metadata,
    render_physical_comparison,
    render_public_json,
    render_status,
    section,
)

_ROOT = Path(__file__).resolve().parents[3]
_MODULE = "Module 7"


@dataclass(frozen=True)
class EvidenceSpec:
    label: str
    shape: str
    record_asset: str
    view_assets: tuple[str, str]
    diagnostic_assets: tuple[str, ...]
    description: str


RECTANGLE_SPECS = (
    EvidenceSpec(
        "Flashcard - validated under equivalent-edge assumption",
        "rectangle",
        "records/experiment_01.json",
        ("images/experiment_01_view1.jpg", "images/experiment_01_view2.jpg"),
        (
            "images/experiment_01_diagnostic.jpg",
        ),
        "Real flashcard width demonstration. Physical validation is limited to the documented rectangular-face equivalence assumption.",
    ),
    EvidenceSpec(
        "FREE ADMISSION - first experiment",
        "rectangle",
        "records/experiment_02.json",
        ("images/experiment_02_view1.jpg", "images/experiment_02_view2.jpg"),
        (
            "images/experiment_02_diagnostic.jpg",
        ),
        "Computed rectangle dimensions with provisional ruler references; neither physical interval passed.",
    ),
    EvidenceSpec(
        "FREE ADMISSION - second experiment",
        "rectangle",
        "records/experiment_03.json",
        ("images/experiment_03_view1.jpg", "images/experiment_03_view2.jpg"),
        (
            "images/experiment_03_diagnostic.jpg",
        ),
        "The rectangle quality gate rejected inconsistent opposite 3D edges. Raw diagnostic lengths are not accepted measurements.",
    ),
    EvidenceSpec(
        "FREE ADMISSION - third experiment",
        "rectangle",
        "records/experiment_04.json",
        ("images/experiment_04_view1.jpg", "images/experiment_04_view2.jpg"),
        (
            "images/experiment_04_diagnostic.jpg",
        ),
        "Geometry gates passed, but both independently verified physical intervals failed.",
    ),
)

CIRCLE_SPECS = (
    EvidenceSpec(
        "Yellow lid - marked perimeter experiment",
        "circle",
        "records/experiment_05.json",
        ("images/experiment_05_view1.jpg", "images/experiment_05_view2.jpg"),
        (
            "images/experiment_05_diagnostic.jpg",
        ),
        "Fourteen marked rim correspondences passed point-level checks, but the circle was rejected by the existing 3D planarity gate.",
    ),
    EvidenceSpec(
        "Yellow lid - unmarked pair pending perimeter correspondence",
        "circle",
        "records/experiment_06.json",
        ("images/experiment_06_view1.jpg", "images/experiment_06_view2.jpg"),
        ("images/experiment_06_diagnostic.jpg",),
        "Checkerboard pose is available, but reliable same-perimeter correspondences were not established. No diameter was produced.",
    ),
)

POLYGON_SPECS = (
    EvidenceSpec(
        "Cardboard triangle - three visible edges",
        "polygon",
        "records/experiment_07.json",
        ("images/experiment_07_view1.jpg", "images/experiment_07_view2.jpg"),
        ("images/experiment_07_diagnostic.jpg",),
        "All three vertices pass point-level geometry gates; the independent physical edge comparisons fail.",
    ),
)


def _render_record(spec: EvidenceSpec) -> None:
    bundle, bundle_error = load_curated_bundle(_ROOT)
    if bundle is None:
        st.error(bundle_error or "The curated evidence bundle is unavailable.")
        st.info("PENDING - restore the curated evidence bundle before this example can be displayed.")
        return
    record_result = bundle.load_record(spec.record_asset)
    if record_result.error:
        st.error(record_result.error)
        st.info("PENDING - supply a valid saved evidence record before this example can be displayed.")
        return
    record = record_result.data or {}
    render_bundled_notice()
    render_status(record.get("status"), record.get("decision") or record.get("validation_decision"))
    st.markdown(spec.description)

    render_image_pair(
        bundle.root,
        list(spec.view_assets),
        ["Stereo View 1 - curated display image", "Stereo View 2 - curated display image"],
    )
    render_diagnostics(bundle.root, list(spec.diagnostic_assets))
    render_metadata(record)

    if spec.shape == "rectangle":
        _render_rectangle(record)
    elif spec.shape == "circle":
        _render_circle(record)
    else:
        _render_polygon(record)
    render_physical_comparison(record, spec.shape)
    render_limitations(record)


def _render_rectangle(record: dict[str, Any]) -> None:
    section("Recovered metric geometry and rectangle dimensions")
    reconstruction = record.get("reconstruction") or record.get("triangulation", {})
    points = reconstruction.get("points_3d_mm") or reconstruction.get("points_3d")
    depths = reconstruction.get("view1_depth_z_mm")
    if points:
        render_3d_table(points, depths, ["top_left", "top_right", "bottom_right", "bottom_left"])
    quality = record.get("rectangle_quality") or record.get("diagnostics", {})
    dimensions = quality.get("dimensions_mm") or quality.get("rectangle_dimensions_mm")
    if dimensions:
        metric_row([(str(label), f"{float(value):.3f} mm") for label, value in dimensions.items()])
    else:
        st.info("No accepted rectangle dimensions are available for this record.")
    if quality:
        render_public_json(quality, caption="Applicable rectangle geometry diagnostics")


def _render_circle(record: dict[str, Any]) -> None:
    st.subheader("Recovered metric geometry and circle diagnostics")
    rim = record.get("rim_reconstruction", {})
    if rim:
        metric_row([
            ("Perimeter points", str(rim.get("landmark_count", "not recorded"))),
            ("Median parallax", f"{float(rim['median_rim_parallax_degrees']):.3f}°" if rim.get("median_rim_parallax_degrees") is not None else "not recorded"),
            ("Depth range", f"{rim.get('depth_range_mm', 'not recorded')} mm"),
        ])
        render_public_json(rim)
    st.error(
        "No accepted stereo diameter is displayed. The marked yellow-lid experiment was rejected "
        "because its 3D rim failed the existing planarity gate; the unmarked pair lacks verified "
        "perimeter correspondences."
    )
    audit = record.get("planarity_gate_audit")
    if audit:
        render_public_json(audit, caption="Planarity-gate evidence")


def _render_polygon(record: dict[str, Any]) -> None:
    st.subheader("Recovered metric geometry and polygon edges")
    triangle = record.get("triangle_reconstruction", {})
    points = triangle.get("vertices_3d_mm")
    if points:
        render_3d_table(points, triangle.get("depths_view1_mm"), ["v0", "v1", "v2"])
    edges = triangle.get("edge_lengths_mm")
    if edges:
        metric_row([(label, f"{float(value):.3f} mm") for label, value in edges.items()])
    else:
        st.info("No polygon edge dimensions are available for this record.")
    if triangle:
        render_public_json(
            {key: value for key, value in triangle.items() if key not in {"vertices_3d_mm"}},
            caption="Applicable polygon geometry diagnostics",
        )


def _overview_page() -> None:
    page_header(
        "Calibrated Stereo Object Measurement",
        "Question 1 demonstrates the existing Module 7 calibrated-stereo workflow: calibrated "
        "camera observations are triangulated into metric 3D points before physical dimensions "
        "are calculated.",
    )
    render_bundled_notice()
    render_bundle_summary(_ROOT)
    st.markdown(
        "The examples below are saved Module 7 experiments. A geometry gate passing is not the "
        "same as independent physical validation; every record retains its original status."
    )
    section("Workflow")
    st.markdown(
        "1. Detect or verify corresponding landmarks in both images.\n"
        "2. Reuse calibrated intrinsics and distortion parameters.\n"
        "3. Recover metric camera pose and triangulate 3D landmarks.\n"
        "4. Check depth, parallax, reprojection, and shape-specific geometry.\n"
        "5. Calculate dimensions only from accepted metric 3D geometry.\n"
        "6. Compare with independent physical measurements without rescaling the reconstruction."
    )
    section("Evidence status")
    st.table([
        {"Shape": "Rectangle", "Examples": "Flashcard; three FREE ADMISSION experiments", "Status": "One validation under an explicit assumption; later accuracy not validated"},
        {"Shape": "Circle", "Examples": "Yellow Enfamil lid", "Status": "No accepted diameter; planarity/correspondence limitations preserved"},
        {"Shape": "Polygon", "Examples": "Cardboard triangle", "Status": "Geometry processed; physical accuracy not validated"},
    ])
    st.info("Room measurement is outside this Question 1 demonstration.")


def _shape_page(title: str, shape: str, specs: tuple[EvidenceSpec, ...]) -> None:
    page_header(
        title,
        {
            "rectangle": "Select a saved rectangle experiment to inspect four-corner triangulation, width/height, and independent physical comparison.",
            "circle": "Select a saved circular experiment to inspect perimeter correspondence, 3D planarity, and the diameter acceptance decision.",
            "polygon": "Inspect the saved triangle experiment: ordered vertices are triangulated first, then each visible 3D edge is measured.",
        }[shape],
    )
    labels = [spec.label for spec in specs]
    selected_label = st.selectbox("Evidence example", labels)
    selected = next(spec for spec in specs if spec.label == selected_label)
    _render_record(selected)


def get_pages() -> tuple[PageSpec, ...]:
    """Return the standalone Module 7 Question 1 pages."""
    return (
        PageSpec(_MODULE, "Overview", 0, _overview_page),
        PageSpec(_MODULE, "Rectangle measurements", 10, lambda: _shape_page("Rectangle measurements", "rectangle", RECTANGLE_SPECS)),
        PageSpec(_MODULE, "Circle measurements", 20, lambda: _shape_page("Circle measurements", "circle", CIRCLE_SPECS)),
        PageSpec(_MODULE, "Polygon measurements", 30, lambda: _shape_page("Polygon measurements", "polygon", POLYGON_SPECS)),
    )
