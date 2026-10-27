"""Validated loading for the curated standalone Question 1 evidence bundle."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BundleRecord:
    """A compact experiment record or a safe user-facing loading error."""

    data: dict[str, Any] | None
    error: str | None = None


@dataclass(frozen=True)
class CuratedEvidenceBundle:
    """Manifest and validated content files for the standalone public preview."""

    root: Path
    manifest: dict[str, Any]
    assets: dict[str, dict[str, Any]]

    def asset_path(self, relative_path: str) -> Path | None:
        """Return a validated asset path, or ``None`` for an unlisted asset."""
        asset = self.assets.get(relative_path)
        if asset is None:
            return None
        return self.root / relative_path

    def load_record(self, relative_path: str) -> BundleRecord:
        """Load one manifest-listed compact JSON record."""
        path = self.asset_path(relative_path)
        asset = self.assets.get(relative_path)
        if path is None or asset is None or asset.get("role") != "compact_evidence_record":
            return BundleRecord(None, "The curated evidence record is unavailable.")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return BundleRecord(None, "The curated evidence record could not be loaded.")
        if not isinstance(value, dict):
            return BundleRecord(None, "The curated evidence record is malformed.")
        return BundleRecord(value)


def _safe_relative_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value or value.startswith("/"):
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def load_curated_bundle(root: Path) -> tuple[CuratedEvidenceBundle | None, str | None]:
    """Validate the manifest, hashes, roles, and files used by the standalone pages."""
    bundle_root = root / "data" / "proposed_public_demo"
    manifest_path = bundle_root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "The curated evidence bundle is missing or malformed."
    if not isinstance(manifest, dict) or not isinstance(manifest.get("publication_approved"), bool):
        return None, "The curated evidence manifest has an invalid approval state."
    entries = manifest.get("assets")
    if not isinstance(entries, list) or manifest.get("asset_count") != len(entries) + 1:
        return None, "The curated evidence manifest has an invalid asset index."

    assets: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            return None, "The curated evidence manifest has a malformed asset entry."
        relative_path = _safe_relative_path(entry.get("relative_path"))
        if relative_path is None or relative_path in assets:
            return None, "The curated evidence manifest has an invalid asset path."
        path = bundle_root / relative_path
        try:
            data = path.read_bytes()
        except OSError:
            return None, "A curated evidence asset is missing."
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or hashlib.sha256(data).hexdigest() != expected_hash:
            return None, "A curated evidence asset failed integrity verification."
        if entry.get("role") not in {"compact_evidence_record", "stereo_view_display", "annotated_diagnostic_display"}:
            return None, "The curated evidence manifest has an unsupported asset role."
        assets[relative_path] = entry
    return CuratedEvidenceBundle(bundle_root, manifest, assets), None
