"""Public-copy-safe rendering helpers for the Module 7 Question 1 pages."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from module7.webapp.design.components import (
    ImageItem,
    image_comparison,
    image_gallery,
    metric_row as design_metric_row,
    page_header as design_page_header,
    result_section,
    status_banner,
)
from module7.webapp.evidence import load_curated_bundle


_HIDDEN_KEYS = {
    "path", "paths", "file", "files", "source", "source_images", "original_inputs",
    "processing_images", "annotated_diagnostics", "correspondence_csv", "csv", "provenance",
    "audit_history", "historical_preservation", "evidence_photographs", "evidence_record",
    "record", "orientation_adjustment", "orientation_normalization", "ruler_evidence",
    "photograph_paths", "accepted_reading_sources",
}


@dataclass(frozen=True)
class EvidenceRecord:
    """A JSON evidence record or a user-visible loading error."""

    path: Path
    data: dict[str, Any] | None
    error: str | None = None


def load_evidence_record(path: Path) -> EvidenceRecord:
    """Load one JSON evidence record without raising into the Streamlit page."""
    try:
        if not path.is_file():
            return EvidenceRecord(path, None, "Evidence record is missing.")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return EvidenceRecord(path, None, "Evidence JSON must contain an object at its root.")
        return EvidenceRecord(path, value)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return EvidenceRecord(path, None, f"Evidence record could not be loaded: {exc}")


def load_bundle_manifest(root: Path) -> dict[str, Any] | None:
    """Load the local proposed evidence manifest, if it has been prepared."""
    bundle, _ = load_curated_bundle(root)
    return bundle.manifest if bundle is not None else None


def resolve_paths(root: Path, paths: list[str]) -> list[Path]:
    """Resolve relative evidence paths while preserving missing paths for diagnostics."""
    return [root / path for path in paths]


def _clean_public_text(value: Any) -> str:
    """Normalize punctuation used in public copy without changing saved evidence."""
    return str(value).replace(chr(0x2014), "-").replace(chr(0x2013), "-")


def _public_value(value: Any, key: str | None = None) -> Any:
    """Return a display-safe subset of a saved JSON value."""
    if key and key.lower() in _HIDDEN_KEYS:
        return None
    if isinstance(value, dict):
        result = {}
        for child_key, child_value in value.items():
            cleaned = _public_value(child_value, child_key)
            if cleaned is not None:
                result[child_key] = cleaned
        return result
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, str):
        return _clean_public_text(value)
    return value


def page_header(title: str, description: str) -> None:
    design_page_header(
        _clean_public_text(title),
        eyebrow="Question 1 / Calibrated stereo",
        description=_clean_public_text(description),
    )


def section(title: str) -> None:
    result_section(_clean_public_text(title))


def status_text(status: str | None) -> str:
    """Map saved machine-readable states to concise public labels."""
    if not status:
        return "Validation pending"
    lowered = status.lower()
    if "circle geometry rejected" in lowered or "planarity quality gate" in lowered:
        return "Circle geometry rejected"
    if "correspondences pending" in lowered or "pending" in lowered:
        return "Validation pending"
    if (
        "physically_validated" in lowered
        or "physical_validation_validated" in lowered
        or "physical validation complete" in lowered
    ):
        return "Validated under stated assumption"
    if "not validated" in lowered or "physical validation pending" in lowered:
        return "Physical accuracy not validated"
    if "validated" in lowered and "checkerboard" in lowered:
        return "Checkerboard pose validated; object validation pending"
    return "Experiment complete"


def _status_explanation(status: str | None, decision: str | None) -> str:
    combined = f"{status or ''} {decision or ''}".lower()
    if "circle geometry rejected" in combined or "planarity" in combined:
        return "The reconstructed rim failed the existing 3D planarity quality gate; no accepted diameter is reported."
    if "correspondences pending" in combined or "pending" in combined:
        return "The available evidence is not sufficient to establish an independent physical validation."
    if "physically_validated" in combined or "physical_validation_validated" in combined:
        return "The comparison is accepted under the documented equivalent rectangular-edge assumption."
    if "not validated" in combined or "physical validation pending" in combined:
        return "Stereo geometry was processed, but the independent physical accuracy criteria were not satisfied."
    if "checkerboard" in combined and "validated" in combined:
        return "The checkerboard pose is usable, but the object measurement remains pending."
    return "The saved experiment record is available for academic review."


def render_status(status: str | None, decision: str | None = None) -> None:
    label = status_text(status)
    lowered = f"{status or ''} {decision or ''}".lower()
    if "rejected" in lowered or "not validated" in lowered or "failed" in lowered:
        kind = "error"
    elif "pending" in lowered or "blocked" in lowered:
        kind = "warning"
    elif "validated" in lowered or "complete" in lowered:
        kind = "success"
    else:
        kind = "info"
    status_banner(kind, f"{label}: {_status_explanation(status, decision)}")


def render_bundled_notice() -> None:
    st.info(
        "These examples use saved Module 7 experiment observations and derived geometry diagnostics. "
        "Computed stereo results are shown separately from independent physical measurements."
    )


def render_bundle_summary(root: Path) -> None:
    manifest = load_bundle_manifest(root)
    if not manifest:
        st.warning("Saved demonstration evidence is unavailable for this page.")
        return
    records = sum(1 for asset in manifest.get("assets", []) if asset.get("role") == "compact_evidence_record")
    st.caption(f"Demonstration coverage: {records} saved experiment records across rectangle, circle, and polygon examples.")


def render_image_pair(root: Path, paths: list[str], captions: list[str]) -> None:
    section("Stereo views")
    items = []
    for index in range(2):
        path = root / paths[index] if index < len(paths) else None
        title = captions[index] if index < len(captions) else f"View {index + 1}"
        if path is not None and path.is_file():
            items.append(ImageItem(str(path), title=_clean_public_text(title)))
        else:
            st.warning(f"{_clean_public_text(title)} is unavailable in this workspace.")
    if len(items) == 2:
        image_comparison(items[0], items[1], width="stretch")


def render_diagnostics(root: Path, paths: list[str]) -> None:
    existing = [path for path in resolve_paths(root, paths) if path.is_file()]
    if not existing:
        st.caption("No annotated diagnostic image is available for this record.")
        return
    section("Annotated correspondences and diagnostics")
    image_gallery(
        [ImageItem(str(path), title="Saved correspondence or geometry diagnostic") for path in existing],
        max_columns=2,
        width="stretch",
    )


def metric_row(values: list[tuple[str, str]]) -> None:
    design_metric_row([(_clean_public_text(label), _clean_public_text(value)) for label, value in values])


def render_metadata(record: dict[str, Any]) -> None:
    section("Calibration and pose metadata")
    calibration = record.get("calibration", {})
    pnp = record.get("checkerboard_pnp", {})
    stereo = record.get("stereo_geometry", {})
    baseline = (
        pnp.get("baseline_mm")
        or pnp.get("relative_translation_metric_mm")
        or record.get("pose_baseline_mm")
        or stereo.get("baseline_mm")
    )
    calibration_id = calibration.get("calibration_id") or record.get("calibration_id") or "not recorded"
    pattern = calibration.get("pattern_size_internal_corners") or calibration.get("pattern_size")
    square = calibration.get("square_size_mm") or calibration.get("square_size")
    pnp_rms = (
        pnp.get("pnp_rms_px")
        or pnp.get("checkerboard_pnp_rms_px")
        or stereo.get("checkerboard_pnp_rms_px")
        or calibration.get("checkerboard_pnp_rms_px")
    )
    if isinstance(calibration_id, str) and "module2-originals-module7" in calibration_id:
        calibration_label = "Module 2 calibration, recomputed in Module 7"
    else:
        calibration_label = _clean_public_text(str(calibration_id))
    metric_row([
        ("Calibration source", "M2 -> M7" if "module2-originals-module7" in str(calibration_id) else "Saved calibration"),
        ("Metric baseline", _format_metric_value("baseline_mm", baseline)),
        ("Checkerboard", f"{pattern[0]} x {pattern[1]}; {float(square):.1f} mm" if isinstance(pattern, (list, tuple)) and len(pattern) == 2 and square is not None else "not recorded"),
    ])
    rows: list[dict[str, Any]] = []
    rows.append({"Metric": "Calibration source", "Value": calibration_label})
    if pnp_rms:
        if isinstance(pnp_rms, dict):
            for label, key in (("PnP RMS view 1", "view1"), ("PnP RMS view 2", "view2")):
                if pnp_rms.get(key) is not None:
                    rows.append({"Metric": label, "Value": _format_metric_value("reprojection_error_px", pnp_rms[key])})
        else:
            rows.append({"Metric": "PnP RMS", "Value": _format_metric_value("reprojection_error_px", pnp_rms)})
    for index, view in enumerate(pnp.get("views", []), start=1):
        error = view.get("pnp_rms_reprojection_error_px") if isinstance(view, dict) else None
        if error is not None and not any(row["Metric"] == f"PnP RMS view {index}" for row in rows):
            rows.append({"Metric": f"PnP RMS view {index}", "Value": _format_metric_value("reprojection_error_px", error)})
    pose_method = record.get("pose_method") or pnp.get("method") or stereo.get("pose_method")
    if pose_method:
        rows.append({"Metric": "Pose method", "Value": _clean_public_text(str(pose_method).replace("checkerboard_pnp", "Checkerboard PnP"))})
    if rows:
        st.table(rows)


def _format_metric_value(key: str, value: Any) -> str:
    if value is None:
        return "not recorded"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        lowered = key.lower()
        if "percentage" in lowered:
            return f"{float(value):.2f}%"
        if "degree" in lowered or "parallax" in lowered:
            return f"{float(value):.2f}°"
        if "mm" in lowered:
            return f"{float(value):.3f} mm"
        if "px" in lowered:
            return f"{float(value):.3f} px"
        return f"{float(value):.3f}"
    if isinstance(value, list) and all(isinstance(item, (int, float)) for item in value):
        if len(value) == 2 and ("interval" in key.lower() or "range" in key.lower()):
            suffix = " mm" if "mm" in key.lower() else ""
            return f"{float(value[0]):.3f} to {float(value[1]):.3f}{suffix}"
        suffix = " mm" if "mm" in key.lower() else ""
        return ", ".join(f"{float(item):.3f}" for item in value) + suffix
    return _clean_public_text(str(value))


def _pretty_label(value: str) -> str:
    return _clean_public_text(value.replace("_", " ").strip().capitalize())


def _flatten_metrics(value: Any, prefix: str = "") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in _HIDDEN_KEYS:
                continue
            child_prefix = f"{prefix} / {_pretty_label(key)}" if prefix else _pretty_label(key)
            rows.extend(_flatten_metrics(child, child_prefix))
    elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
        for index, child in enumerate(value, start=1):
            rows.extend(_flatten_metrics(child, f"{prefix} {index}"))
    elif isinstance(value, (list, tuple)) and len(value) <= 8 and all(isinstance(item, (int, float)) for item in value):
        rows.append({"Metric": prefix, "Value": _format_metric_value(prefix, list(value))})
    elif value is not None:
        rows.append({"Metric": prefix, "Value": _format_metric_value(prefix, value)})
    return rows


def diagnostic_table(rows: list[tuple[str, Any]]) -> None:
    values = [{"Diagnostic": _clean_public_text(label), "Value": _format_metric_value(label, value)} for label, value in rows if value is not None]
    if values:
        st.table(values)


def render_3d_table(points: Any, depths: Any = None, labels: list[str] | None = None) -> None:
    if not isinstance(points, list):
        return
    rows = []
    for index, point in enumerate(points):
        if not isinstance(point, list) or len(point) < 3:
            continue
        row = {"Landmark": labels[index] if labels and index < len(labels) else f"p{index}"}
        row.update({
            "X (mm)": f"{float(point[0]):.3f}",
            "Y (mm)": f"{float(point[1]):.3f}",
            "Z / depth (mm)": f"{float(point[2]):.3f}",
        })
        if isinstance(depths, list) and index < len(depths):
            row["Depth record (mm)"] = f"{float(depths[index]):.3f}"
        rows.append(row)
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")


def rectangle_geometry_state(record: dict[str, Any]) -> tuple[str, bool, str]:
    """Classify rectangle values without changing the saved experiment status."""
    gate = record.get("rectangle_quality_gate")
    if isinstance(gate, dict) and gate.get("accepted") is False:
        return (
            "Diagnostic reconstruction only",
            False,
            "The rectangle quality gate rejected the geometry; displayed lengths are not accepted measurements.",
        )
    quality = record.get("rectangle_quality")
    if isinstance(quality, dict) and quality.get("all_existing_shape_gates_passed") is True:
        return (
            "Geometry accepted",
            True,
            "The saved rectangle geometry gates passed; independent physical accuracy is reported separately.",
        )
    point_quality = record.get("quality")
    if isinstance(point_quality, dict) and point_quality.get("all_points_valid") is True:
        return (
            "Geometry accepted",
            True,
            "Finite triangulation, positive depth, parallax, and reprojection checks passed for this segment.",
        )
    diagnostics = record.get("diagnostics")
    if isinstance(diagnostics, dict):
        return (
            "Computed geometry; shape-level gate not recorded",
            False,
            "Point-level diagnostics are preserved, but this saved record does not mark a rectangle shape-level result as accepted.",
        )
    return ("Geometry not accepted", False, "No accepted rectangle geometry is recorded for this example.")


def _physical_reference(value: Any, interval: Any = None, uncertainty: Any = None) -> str:
    if value is None:
        return "Not recorded"
    text = f"{float(value):.2f} mm"
    if uncertainty is not None:
        text += f" +/- {float(uncertainty):.2f} mm"
    if isinstance(interval, list) and len(interval) == 2:
        text += f" ({float(interval[0]):.2f}-{float(interval[1]):.2f} mm)"
    return text


def _rectangle_comparison_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    _, geometry_accepted, _ = rectangle_geometry_state(record)
    ground_truth = record.get("ground_truth") or record.get("physical_measurements") or {}
    comparison = record.get("comparison") or {}
    rows: list[dict[str, str]] = []

    if "actual_length_mm" in ground_truth:
        reconstruction = record.get("reconstruction", {})
        rows.append({
            "Dimension": "Flashcard width",
            "Physical reference": _physical_reference(
                ground_truth.get("actual_length_mm"),
                ground_truth.get("reference_interval_mm"),
                ground_truth.get("uncertainty_mm"),
            ),
            "Stereo result": f"{float(reconstruction.get('euclidean_segment_length_mm')):.3f} mm" if geometry_accepted and reconstruction.get("euclidean_segment_length_mm") is not None else "Not accepted",
            "Absolute error": f"{float(comparison.get('absolute_error_mm')):.3f} mm" if geometry_accepted and comparison.get("absolute_error_mm") is not None else "Not reported",
            "% error": _format_metric_value("percentage_error", comparison.get("percentage_error")) if geometry_accepted else "Not reported",
            "Interval": "Inside" if comparison.get("within_reference_interval") is True else "Outside" if comparison else "Not assessed",
            "Interpretation": "Validated under stated assumption" if geometry_accepted and comparison.get("within_reference_interval") is True else "Physical validation not established",
        })
        return rows

    physical = ground_truth
    if not isinstance(comparison, dict):
        return rows

    entries: list[tuple[str, dict[str, Any], str, Any, Any, Any]] = []
    if "long_side" in comparison:
        entries = [
            ("Long side", comparison["long_side"], "long_side_mean_mm", physical.get("reference_intervals_mm", {}).get("long_side"), physical.get("provisional_uncertainty_mm")),
            ("Short side", comparison.get("short_side", {}), "short_side_mean_mm", physical.get("reference_intervals_mm", {}).get("short_side"), physical.get("provisional_uncertainty_mm")),
        ]
    elif "reconstructed_image_order_side_edge_vs_physical_long_dimension" in comparison:
        entries = [
            ("Long side", comparison["reconstructed_image_order_side_edge_vs_physical_long_dimension"], "reported_width_mean_mm", physical.get("reference_intervals_mm", {}).get("width"), physical.get("uncertainty_mm")),
            ("Short side", comparison["reconstructed_image_order_top_edge_vs_physical_short_dimension"], "reported_height_mean_mm", physical.get("reference_intervals_mm", {}).get("height"), physical.get("uncertainty_mm")),
        ]
    else:
        diagnostic = comparison.get("ungated_diagnostic_only", {})
        for key, entry in diagnostic.items():
            if not isinstance(entry, dict):
                continue
            label = "Long side" if "long_side" in key or "long_side" in key else "Short side"
            if "height" in key:
                label = "Long side"
            elif "width" in key:
                label = "Short side"
            entries.append((label, entry, "", entry.get("reference_interval_mm"), None))

    for label, entry, physical_key, interval, uncertainty in entries:
        if not isinstance(entry, dict):
            continue
        physical_value = entry.get("physical_mean_mm")
        if physical_value is None and physical_key:
            physical_value = physical.get(physical_key)
        rows.append({
            "Dimension": label,
            "Physical reference": _physical_reference(physical_value, interval, uncertainty),
            "Stereo result": (
                f"{float(entry.get('reconstructed_mm')):.3f} mm" if entry.get("reconstructed_mm") is not None else "Not produced"
            ) + (" (diagnostic)" if not geometry_accepted else ""),
            "Absolute error": f"{float(entry.get('absolute_error_mm')):.3f} mm" if entry.get("absolute_error_mm") is not None else "Not reported",
            "% error": _format_metric_value("percentage_error", entry.get("percentage_error")),
            "Interval": "Inside" if entry.get("inside_reference_interval") is True else "Outside" if entry.get("inside_reference_interval") is False else "Not assessed",
            "Interpretation": "Accepted geometry; physical accuracy not validated" if geometry_accepted else "Diagnostic only; geometry not accepted",
        })
    return rows


def _circle_reference_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    physical = record.get("physical_measurement") or {}
    if not physical:
        return [{
            "Metric": "Physical diameter",
            "Value": "Not recorded",
            "Interpretation": "Pending independent physical measurement and perimeter correspondence",
        }]
    return [
        {"Metric": "Physical diameter", "Value": _physical_reference(physical.get("mean_diameter_mm"), physical.get("reference_interval_mm"), physical.get("uncertainty_mm")), "Interpretation": "Documented physical reference"},
        {"Metric": "Stereo diameter", "Value": "Not accepted", "Interpretation": "Circle geometry rejected by the 3D planarity gate"},
        {"Metric": "Validation outcome", "Value": "Not validated", "Interpretation": "No accepted stereo diameter was produced"},
    ]


def _polygon_comparison_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    physical = record.get("physical_measurements", {})
    for entry in record.get("comparisons", []):
        if not isinstance(entry, dict):
            continue
        rows.append({
            "Dimension": entry.get("edge_id", "edge"),
            "Physical reference": _physical_reference(entry.get("physical_mean_mm"), entry.get("reference_interval_mm"), entry.get("uncertainty_mm", physical.get("uncertainty_mm"))),
            "Stereo result": f"{float(entry.get('reconstructed_length_mm')):.3f} mm" if entry.get("reconstructed_length_mm") is not None else "Not produced",
            "Absolute error": f"{float(entry.get('absolute_error_mm')):.3f} mm" if entry.get("absolute_error_mm") is not None else "Not reported",
            "% error": _format_metric_value("percentage_error", entry.get("percentage_error")),
            "Interval": "Inside" if entry.get("within_reference_interval") is True else "Outside" if entry.get("within_reference_interval") is False else "Not assessed",
            "Interpretation": "Physical accuracy not validated",
        })
    return rows


def render_physical_comparison(record: dict[str, Any], shape: str) -> None:
    section("Independent physical reference and comparison")
    ground_truth = record.get("ground_truth") or record.get("physical_measurements") or record.get("physical_measurement")
    comparison = record.get("comparison") or record.get("comparisons")
    if shape == "rectangle":
        rows = _rectangle_comparison_rows(record)
        if rows:
            st.table(rows)
        else:
            st.warning("PENDING - no independent physical comparison is recorded for this rectangle.")
    elif shape == "circle":
        st.table(_circle_reference_rows(record))
    elif shape == "polygon":
        rows = _polygon_comparison_rows(record)
        if rows:
            st.table(rows)
        else:
            st.warning("PENDING - no independent physical comparison is recorded for this polygon.")
    elif ground_truth is None:
        st.warning("PENDING - no independent physical reference is recorded for this evidence set.")
    else:
        st.table(_flatten_metrics(_public_value(ground_truth), "Physical reference"))
    if ground_truth is not None or comparison is not None:
        render_public_json(
            {"physical_reference": ground_truth, "comparison": comparison},
            caption="Full physical comparison record",
        )


def render_limitations(record: dict[str, Any]) -> None:
    limitations = record.get("limitations")
    if limitations:
        section("Limitations and assumptions")
        if isinstance(limitations, list):
            for item in limitations:
                st.markdown(f"- {_clean_public_text(item)}")
        elif isinstance(limitations, str):
            st.write(_clean_public_text(limitations))


def render_public_json(value: Any, *, caption: str | None = None) -> None:
    """Keep the full academic diagnostic record available behind a collapsed detail panel."""
    label = _clean_public_text(caption or "Technical diagnostic record")
    with st.expander(label, expanded=False):
        st.json(_public_value(value), expanded=False)
