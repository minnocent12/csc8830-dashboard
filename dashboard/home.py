"""Home view of the combined CSc 8830 dashboard.

Content lives here, not in the shared design kit: the kit provides components and the shell,
this module provides the course description and module metadata.

Card data comes from three sources, each with one job:
* ``MODULE_INFO``: display title and description per module label (navigation copy only)
* the page registry, via the shell's ``HomeContext``: which modules exist, their page
  counts, and each module's default destination (its first registered page)
* optional ``get_module_summary()`` providers exposed by modules: one status chip backed by
  that module's own committed evidence. A missing provider or a ``None`` result shows no chip.
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import streamlit as st

from dashboard.design.components import (
    StatusKind,
    card,
    eyebrow,
    page_header,
    section_header,
    status_chip,
)
from dashboard.design.navigation import NavModule
from dashboard.design.shell import HomeContext

LOGGER = logging.getLogger(__name__)

HOME_TITLE = "CSc 8830 Computer Vision"
HOME_DESCRIPTION = (
    "Interactive computer vision experiments covering camera calibration, image processing, "
    "human boundary detection, motion analysis and 3D reconstruction."
)
CARD_COLUMNS = 2
OPEN_LABEL = "Open Module"

SummaryProvider = Callable[[], Any]


@dataclass(frozen=True)
class ModuleInfo:
    """Navigation copy for one module, keyed by its registered ``module_label``."""

    label: str
    title: str
    description: str


MODULE_INFO: tuple[ModuleInfo, ...] = (
    ModuleInfo(
        "Module 2",
        "Camera Calibration & Measurement",
        "Camera calibration, perspective geometry, physical dimension estimation and validation.",
    ),
    ModuleInfo(
        "Module 3",
        "Spatial & Fourier Image Processing",
        "Image blurring, spatial and frequency-domain filtering, experimental validation and "
        "convolution theory.",
    ),
    ModuleInfo(
        "Module 4",
        "Human Boundary Detection",
        "Classical RGB and thermal human segmentation, quantitative evaluation and "
        "Fourier-domain analysis.",
    ),
    ModuleInfo(
        "Module 5-6",
        "Motion & 3D Reconstruction",
        "Optical flow, feature tracking, bilinear interpolation and multi-view planar "
        "reconstruction.",
    ),
)


@dataclass(frozen=True)
class HomeCard:
    """Everything one module card shows."""

    label: str
    slug: str
    title: str
    description: str
    page_count: int
    first_page: str
    status: tuple[str, str] | None  # (label, chip kind) or no chip


def _status(provider: SummaryProvider | None, module_label: str) -> tuple[str, str] | None:
    """Call a module's optional summary provider; anything unusable means no chip."""
    if provider is None:
        return None
    try:
        summary = provider()
    except Exception:  # a broken optional provider must never take Home down
        LOGGER.warning("Module summary provider for %s failed", module_label, exc_info=True)
        return None
    if summary is None:
        return None
    label, kind = str(getattr(summary, "label", "")).strip(), getattr(summary, "kind", None)
    if not label or kind not in {k.value for k in StatusKind}:
        LOGGER.warning("Ignoring malformed module summary for %s: %r", module_label, summary)
        return None
    return label, kind


def build_cards(
    modules: Sequence[NavModule],
    summaries: Mapping[str, SummaryProvider] | None = None,
    info: Sequence[ModuleInfo] = MODULE_INFO,
) -> list[HomeCard]:
    """One card per registered module, in registry order. The registry is authoritative."""
    by_label = {item.label: item for item in info}
    summaries = summaries or {}
    cards = []
    for module in modules:
        meta = by_label.get(module.label)
        cards.append(
            HomeCard(
                label=module.label,
                slug=module.slug,
                title=meta.title if meta else module.label,
                description=meta.description if meta else "",
                page_count=len(module.pages),
                first_page=module.pages[0].label,
                status=_status(summaries.get(module.label), module.label),
            )
        )
    return cards


def _render_card(home: HomeCard, context: HomeContext) -> None:
    with card():
        eyebrow(home.label)
        st.markdown(f"#### {home.title}")
        if home.description:
            st.markdown(home.description)
        st.caption(f"{home.page_count} page{'s' if home.page_count != 1 else ''}")
        if home.status:
            status_chip(*home.status)
        st.button(
            OPEN_LABEL,
            key=f"home_open_{home.slug}",
            help=f"Opens {home.label} at {home.first_page}",
            on_click=context.open_module,
            args=(home.slug,),
        )


def make_home_renderer(
    summaries: Mapping[str, SummaryProvider] | None = None,
) -> Callable[[HomeContext], None]:
    """Build the Home renderer the shell calls with its ``HomeContext``."""

    def render_home(context: HomeContext) -> None:
        page_header(HOME_TITLE, description=HOME_DESCRIPTION)
        section_header("Explore Modules")
        cards = build_cards(context.modules, summaries)
        for start in range(0, len(cards), CARD_COLUMNS):
            row = cards[start : start + CARD_COLUMNS]
            for column, home in zip(st.columns(CARD_COLUMNS), row):
                with column:
                    _render_card(home, context)

    return render_home
