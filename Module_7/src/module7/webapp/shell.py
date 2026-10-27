"""Thin standalone adapter around the vendored CSc 8830 UI shell."""
from __future__ import annotations

from collections.abc import Sequence

from module7.webapp._page import PageSpec
from module7.webapp.design.shell import render_shell


def render_app(pages: Sequence[PageSpec], *, title: str = "CSc 8830 - Module 7") -> None:
    """Render Module 7 through the shared standalone shell."""
    render_shell(pages, page_title=title, standalone=True)
