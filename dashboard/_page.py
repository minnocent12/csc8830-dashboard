"""Page contract used by the root course dashboard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

RenderFn = Callable[[], None]


@dataclass(frozen=True)
class DashboardPage:
    """One page contributed by a module to the root dashboard."""

    module_label: str
    page_label: str
    order: int
    render: RenderFn
