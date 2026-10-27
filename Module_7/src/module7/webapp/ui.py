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
    """Return a stable human-readable status label without upgrading evidence."""
    if not status:
        return "PENDING - no validation status recorded"
    return _clean_public_text(status)


def render_status(status: str | None, decision: str | None = None) -> None:
    text = status_text(status)
    lowered = text.lower()
    if "rejected" in lowered or "not validated" in lowered or "failed" in lowered:
        kind = "error"
    elif "pending" in lowered or "blocked" in lowered:
        kind = "warning"
    elif "validated" in lowered or "complete" in lowered:
        kind = "success"
    else:
        kind = "info"
    status_banner(kind, f"Validation status: {text}")
    if decision:
        st.caption(f"Decision record: {_clean_public_text(decision)}")


def render_bundled_notice() -> None:
    st.info(
        "Genuine saved experiment evidence is displayed from the curated bundle. Its publication "
        "status is recorded in the bundle manifest; no deployment is performed by this app."
    )


def render_bundle_summary(root: Path) -> None:
    manifest = load_bundle_manifest(root)
    if not manifest:
        st.warning("The proposed public evidence bundle has not been prepared yet.")
        return
    assets = manifest.get("assets", [])
    size_mb = float(manifest.get("total_size_bytes", 0)) / 1_000_000
    approval = "publication approval pending" if not manifest.get("publication_approved") else "approved"
    file_count = manifest.get("asset_count", len(assets) + 1)
    st.caption(f"Curated evidence bundle: {file_count} files, {size_mb:.2f} MB; {approval}.")


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
    pnp_rms = pnp.get("pnp_rms_px") or stereo.get("checkerboard_pnp_rms_px")
    metric_row([
        ("Calibration", str(calibration_id)),
        ("Metric baseline", f"{float(baseline):.3f} mm" if baseline is not None else "not recorded"),
        ("Checkerboard", f"{pattern}, {square} mm" if pattern and square else "not recorded"),
    ])
    rows: list[dict[str, Any]] = []
    if pnp_rms:
        if isinstance(pnp_rms, dict):
            for label, key in (("PnP RMS view 1", "view1"), ("PnP RMS view 2", "view2")):
                if pnp_rms.get(key) is not None:
                    rows.append({"Metric": label, "Value": f"{float(pnp_rms[key]):.6f} px"})
        else:
            rows.append({"Metric": "PnP RMS", "Value": str(pnp_rms)})
    pose_method = record.get("pose_method") or pnp.get("method") or stereo.get("pose_method")
    if pose_method:
        rows.append({"Metric": "Pose method", "Value": _clean_public_text(pose_method)})
    if rows:
        st.table(rows)


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
        st.json(_public_value(ground_truth), expanded=False)
    if comparison is None:
        st.info("No accepted physical comparison is available for this record.")
    else:
        st.caption(f"{shape.title()} comparison record")
        st.json(_public_value(comparison), expanded=False)


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
    """Render selected academic metadata after removing provenance-only fields."""
    if caption:
        st.caption(_clean_public_text(caption))
    st.json(_public_value(value), expanded=False)
