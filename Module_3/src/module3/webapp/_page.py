"""The page-provider contract shared by the standalone app and future dashboards."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

RenderFn = Callable[[], None]


@dataclass(frozen=True)
class PageSpec:
    """One selectable page in a Streamlit app."""

    module_label: str
    page_label: str
    order: int
    render: RenderFn
