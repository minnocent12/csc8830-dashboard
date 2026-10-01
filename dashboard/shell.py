"""Streamlit shell for the combined course dashboard: an adapter over the shared shell.

Navigation, identity, breadcrumbs, footer, and the ``?module=...&page=...`` deep links come
from ``dashboard.design.shell``, a vendored copy of the csc8830-ui design kit. The Home view
and its content come from ``dashboard.home``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from dashboard._page import DashboardPage
from dashboard.design.shell import HomeSpec, render_shell
from dashboard.home import make_home_renderer

# Category label above the top-level selectbox. "Explore" rather than "Module" because the
# list starts with Home, which is not a module (chosen from Home screenshots).
TOP_NAV_LABEL = "Explore"


def render_app(
    pages: Sequence[DashboardPage],
    *,
    title: str = "CSc 8830 Computer Vision",
    notices: Sequence[str] = (),
    summaries: Mapping[str, Callable[[], Any]] | None = None,
) -> None:
    """Render Home and all module pages in one app with URL-synchronized navigation."""
    render_shell(
        pages,
        page_title=title,
        sync_query_params=True,
        home=HomeSpec(render=make_home_renderer(summaries)),
        top_nav_label=TOP_NAV_LABEL,
        notices=notices,
        empty_message="No module pages are registered.",
    )
