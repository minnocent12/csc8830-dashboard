"""The page-provider contract used by the standalone app and future dashboards."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

RenderFn = Callable[[], None]


@dataclass(frozen=True)
class PageSpec:
    """One selectable Streamlit page."""

    module_label: str
    page_label: str
    order: int
    render: RenderFn
