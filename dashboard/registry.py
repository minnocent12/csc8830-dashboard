"""Structural page-provider adapter for the root course dashboard."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from dashboard._page import DashboardPage

PageProvider = Callable[[], Iterable[Any]]


def _adapt_page(page: Any) -> DashboardPage:
    """Convert a module-specific PageSpec-like object into a dashboard page.

    Module 2 and Module 3 each define their own ``PageSpec`` class so that each repository is
    independently submittable. The root dashboard accepts the shared attribute shape instead of
    requiring one shared class.
    """
    missing = [
        name
        for name in ("module_label", "page_label", "order", "render")
        if not hasattr(page, name)
    ]
    if missing:
        raise TypeError(f"page {page!r} is missing required attributes: {', '.join(missing)}")
    render = getattr(page, "render")
    if not callable(render):
        raise TypeError(f"page {page!r} has a non-callable render attribute")
    return DashboardPage(
        module_label=str(getattr(page, "module_label")),
        page_label=str(getattr(page, "page_label")),
        order=int(getattr(page, "order")),
        render=render,
    )


def collect_pages(providers: Sequence[PageProvider]) -> list[DashboardPage]:
    """Merge module page providers into one ordered, de-duplicated dashboard list."""
    merged: dict[tuple[str, str], DashboardPage] = {}
    for provider in providers:
        for page in provider():
            adapted = _adapt_page(page)
            merged[(adapted.module_label, adapted.page_label)] = adapted
    return sorted(merged.values(), key=lambda p: (p.module_label, p.order, p.page_label))
