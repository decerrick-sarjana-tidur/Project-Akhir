"""
compat.py
---------
Small shim layer so the rest of the app doesn't crash if this Flet
installation names things slightly differently than expected.

Flet has, at various versions, used:
  - lowercase module-style helpers: ft.margin.only(...), ft.padding.only(...),
    ft.border_radius.only(...), ft.border.all(...), ft.alignment.center
  - capitalized class-style helpers: ft.Margin.only(...), ft.Padding.only(...),
    ft.BorderRadius.only(...), ft.Border.all(...), ft.Alignment.CENTER
  - ft.icons.xxx (lowercase) vs ft.Icons.XXX (capitalized) for Material icons

This module resolves whichever is actually available at import time so a
single codebase works across both styles without guessing wrong and crashing
on the very first Container().
"""
import flet as ft

Margin = getattr(ft, "Margin", None) or ft.margin
Padding = getattr(ft, "Padding", None) or ft.padding
BorderRadius = getattr(ft, "BorderRadius", None) or ft.border_radius
Border = getattr(ft, "Border", None) or ft.border
BorderSide = getattr(ft, "BorderSide", None)

_AlignmentClass = getattr(ft, "Alignment", None)
_alignment_mod = getattr(ft, "alignment", None)

_IconsClass = getattr(ft, "Icons", None) or getattr(ft, "icons", None)


def align(name: str):
    """name like 'CENTER', 'TOP_LEFT', 'BOTTOM_RIGHT', 'CENTER_LEFT'..."""
    if _AlignmentClass is not None and hasattr(_AlignmentClass, name):
        return getattr(_AlignmentClass, name)
    if _alignment_mod is not None and hasattr(_alignment_mod, name.lower()):
        return getattr(_alignment_mod, name.lower())
    # last-resort manual fallback
    manual = {
        "CENTER": ft.alignment.center if _alignment_mod else None,
    }
    return manual.get(name)


def icon(name: str, fallback: str = "HELP_OUTLINE_ROUNDED"):
    """Resolve a Material icon by name, tolerant of missing exact variants."""
    if _IconsClass is None:
        return None
    val = getattr(_IconsClass, name, None)
    if val is None:
        val = getattr(_IconsClass, fallback, None)
    if val is None:
        # try a non-rounded version of the same icon as a last resort
        base = name.replace("_ROUNDED", "").replace("_OUTLINED", "")
        val = getattr(_IconsClass, base, None)
    return val


def font_weight(name: str):
    fw = getattr(ft, "FontWeight", None)
    if fw is not None and hasattr(fw, name):
        return getattr(fw, name)
    return None


def top_colored_border(top_color: str, side_color: str, top_width: int = 2, side_width: int = 1):
    """Border with a coloured top edge + neutral sides/bottom.

    Mirrors the JSX pattern:  border: `1px solid ${T.surfaceBorder}`,
                               borderTop: `2px solid ${cat.color}`

    Falls back to a plain all-sides border if BorderSide is unavailable.
    """
    if BorderSide is None:
        return Border.all(side_width, side_color)
    return ft.Border(
        top=BorderSide(top_width, top_color),
        left=BorderSide(side_width, side_color),
        right=BorderSide(side_width, side_color),
        bottom=BorderSide(side_width, side_color),
    )


def safe_run_task(page: ft.Page, coro):
    """Best-effort background task scheduling across Flet versions."""
    try:
        page.run_task(coro)
    except Exception:
        pass


async def run_in_thread(func, *args):
    """Run a synchronous blocking function in a thread-pool executor.

    Lets us call synchronous SDK operations from an async context
    without freezing Flet's UI event loop.

    Compatible with Python 3.7+ — uses asyncio.to_thread on 3.9+,
    falls back to loop.run_in_executor on older versions.
    """
    import asyncio
    import sys
    import functools
    if sys.version_info >= (3, 9):
        return await asyncio.to_thread(func, *args)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args))
