"""Root Streamlit dashboard for the CSc 8830 assignment workspace.

Run from the ``Assignments/`` directory:

    streamlit run app.py

The dashboard imports page providers from each implemented module. Each module remains
independently runnable through its own ``Module_*/app.py`` entry point.
"""
from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for _src in sorted(_ROOT.glob("Module_*/src")):
    if _src.is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from dashboard.registry import PageProvider, collect_pages  # noqa: E402
from dashboard.shell import render_app  # noqa: E402

_MODULE_PAGE_MODULES = (
    ("Module 2", "module2.webapp.pages"),
    ("Module 3", "module3.webapp.pages"),
    ("Module 4", "module4.webapp.pages"),
)


def discover_page_providers() -> tuple[list[PageProvider], list[str]]:
    """Import implemented module page providers and report missing future modules."""
    providers: list[PageProvider] = []
    notices: list[str] = []
    for module_label, import_path in _MODULE_PAGE_MODULES:
        try:
            module = importlib.import_module(import_path)
        except ModuleNotFoundError as exc:
            top_level = import_path.split(".", maxsplit=1)[0]
            if exc.name == top_level:
                notices.append(f"{module_label} is not importable yet; skipping it.")
                continue
            raise
        get_pages = getattr(module, "get_pages", None)
        if not callable(get_pages):
            notices.append(f"{module_label} does not expose a callable get_pages(); skipping it.")
            continue
        providers.append(get_pages)
    return providers, notices


def main() -> None:
    """Render the combined course dashboard."""
    providers, notices = discover_page_providers()
    render_app(collect_pages(providers), notices=notices)


if __name__ == "__main__":
    main()
