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
        ("Calibration source", calibration_label),
        ("Metric baseline", _format_metric_value("baseline_mm", baseline)),
        ("Checkerboard", f"{pattern[0]} x {pattern[1]} corners; {float(square):.1f} mm squares" if isinstance(pattern, (list, tuple)) and len(pattern) == 2 and square is not None else "not recorded"),
    ])
    rows: list[dict[str, Any]] = []
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
        if len(value) == 2 and "interval" in key.lower():
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
        row.update({"X (mm)": point[0], "Y (mm)": point[1], "Z / depth (mm)": point[2]})
        if isinstance(depths, list) and index < len(depths):
            row["Depth record (mm)"] = depths[index]
        rows.append(row)
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")


def render_physical_comparison(record: dict[str, Any], shape: str) -> None:
    section("Independent physical reference and comparison")
    ground_truth = record.get("ground_truth") or record.get("physical_measurements") or record.get("physical_measurement")
    comparison = record.get("comparison") or record.get("comparisons")
    if ground_truth is None:
        st.warning("PENDING - no independent physical reference is recorded for this evidence set.")
    else:
        st.table(_flatten_metrics(_public_value(ground_truth), "Physical reference"))
    if comparison is None:
        st.info("No accepted physical comparison is available for this record.")
    else:
        st.caption(f"{shape.title()} comparison record")
        rows = _flatten_metrics(_public_value(comparison), "Comparison")
        if rows:
            st.table(rows)
        render_public_json(comparison, caption="Technical comparison record")


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
