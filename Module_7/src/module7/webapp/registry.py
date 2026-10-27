"""Provider validation and stable page ordering."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Callable

from module7.webapp._page import PageSpec

PageProvider = Callable[[], Iterable[PageSpec]]


def collect_pages(providers: Sequence[PageProvider]) -> list[PageSpec]:
    """Merge providers and reject malformed or duplicate page identities."""
    pages: dict[tuple[str, str], PageSpec] = {}
    for provider in providers:
        for page in provider():
            if not isinstance(page, PageSpec):
                raise TypeError(f"provider {provider!r} yielded {type(page)!r}, expected PageSpec")
            identity = (page.module_label, page.page_label)
            if identity in pages:
                raise ValueError(f"duplicate page identity: {identity}")
            if not callable(page.render):
                raise TypeError(f"page {identity} has a non-callable render function")
            pages[identity] = page
    return sorted(pages.values(), key=lambda page: (page.order, page.page_label))
