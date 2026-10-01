"""Streamlit shell for the combined course dashboard: an adapter over the shared shell.

Navigation, identity, breadcrumbs, footer, and the ``?module=...&page=...`` deep links come
from ``dashboard.design.shell``, a vendored copy of the csc8830-ui design kit.
"""
from __future__ import annotations

from collections.abc import Sequence

from dashboard._page import DashboardPage
from dashboard.design.shell import render_shell


def render_app(
    pages: Sequence[DashboardPage],
    *,
    title: str = "CSc 8830 Computer Vision",
    notices: Sequence[str] = (),
) -> None:
    """Render all module pages in one app with URL-synchronized navigation."""
    render_shell(
        pages,
        page_title=title,
        sync_query_params=True,
        notices=notices,
        empty_message="No module pages are registered.",
    )
