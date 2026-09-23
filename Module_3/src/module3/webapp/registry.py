"""Provider-agnostic page collection."""
from __future__ import annotations

from typing import Callable, Iterable, Sequence

from module3.webapp._page import PageSpec

PageProvider = Callable[[], Iterable[PageSpec]]


def collect_pages(providers: Sequence[PageProvider]) -> list[PageSpec]:
    """Merge pages from providers into a stable, de-duplicated, ordered list."""
    merged: dict[tuple[str, str], PageSpec] = {}
    for provider in providers:
        for page in provider():
            if not isinstance(page, PageSpec):
                raise TypeError(f"provider {provider!r} yielded {type(page)!r}, expected PageSpec")
            merged[(page.module_label, page.page_label)] = page
    return sorted(merged.values(), key=lambda p: (p.module_label, p.order, p.page_label))
