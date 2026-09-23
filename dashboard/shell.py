"""Streamlit shell for the root course dashboard."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

import streamlit as st

from dashboard._page import DashboardPage


def render_app(
    pages: Sequence[DashboardPage],
    *,
    title: str = "CSc 8830 Computer Vision",
    notices: Sequence[str] = (),
) -> None:
    """Render all module pages in one sidebar-driven Streamlit app."""
    st.set_page_config(page_title=title, layout="wide")

    if not pages:
        st.error("No module pages are registered.")
        for notice in notices:
            st.info(notice)
        return

    by_module: dict[str, list[DashboardPage]] = defaultdict(list)
    for page in pages:
        by_module[page.module_label].append(page)

    with st.sidebar:
        st.title(title)
        module_label = st.selectbox("Module", list(by_module))
        module_pages = by_module[module_label]
        page_label = st.radio("Page", [p.page_label for p in module_pages])
        if notices:
            with st.expander("Dashboard notices"):
                for notice in notices:
                    st.caption(notice)

    selected = next(p for p in module_pages if p.page_label == page_label)
    selected.render()
