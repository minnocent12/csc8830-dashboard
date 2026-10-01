"""Optional Home-page summary for the combined CSc 8830 course dashboard.

The combined dashboard may call ``get_module_summary()`` to show one status chip on this
module's Home card. The standalone app never uses it.

Evidence contract: the summary reports "Results available" only when the committed
experiment results table has the expected columns and at least one data row. Otherwise it
returns ``None`` and no chip is shown. It only reads that small committed file: it never
filters images, recomputes errors, judges result quality, writes files, or touches the
network.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

RESULTS_TABLE = "results/experiment_results.csv"
REQUIRED_COLUMNS = frozenset({"experiment", "filter", "kernel_size", "mae", "mse"})


@dataclass(frozen=True)
class ModuleSummary:
    """One status chip: ``kind`` is a shared chip kind (neutral, info, success, warning, error)."""

    label: str
    kind: str


RESULTS_AVAILABLE = ModuleSummary("Results available", "success")


def get_module_summary(repo_root: Path | None = None) -> ModuleSummary | None:
    """Return the Home status for this module, or ``None`` when the evidence is incomplete."""
    path = (repo_root or _REPO_ROOT) / RESULTS_TABLE
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not REQUIRED_COLUMNS <= set(reader.fieldnames or ()):
                return None
            has_row = any(any((value or "").strip() for value in row.values()) for row in reader)
    except (OSError, csv.Error):
        return None
    return RESULTS_AVAILABLE if has_row else None
