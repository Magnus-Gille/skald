"""Hourly tick — compose a fresh verse, gather a footer, push to the display."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import layout
from .compose import VerseContext, compose
from .display import get_display
from .state import State
from .weather import fetch as fetch_weather, footer_line


def run_tick(
    dry_run: bool = False,
    out_path: Optional[Path] = None,
    force_full: bool = False,
    note: Optional[str] = None,
) -> dict:
    """Compose, render, push. Returns a dict summary."""
    state = State.load()
    now = datetime.now()

    weather = fetch_weather()
    weather_summary = (
        f"{round(weather.temp_c)}° {weather.summary}" if weather else None
    )

    project_note = note or os.environ.get("SKALD_NOTE")

    ctx = VerseContext(
        when=now,
        weather_summary=weather_summary,
        project_note=project_note,
        recent_verses=state.recent_verses,
    )
    lines, source, stale = compose(ctx)

    state.verse = lines
    state.verse_source = source
    state.verse_stale = stale
    state.remember_verse(lines)

    footer = footer_line(weather, extra=None)
    state.footer = footer
    state.footer_source = "tick"

    img = layout.render(verse=lines, footer=footer, now=now)
    full = force_full or state.needs_full_refresh()
    disp = get_display(dry_run=dry_run, out_path=out_path)
    disp.show(img, partial=not full)
    state.record_refresh(partial=not full)
    state.save()

    return {
        "verse": lines,
        "source": source,
        "stale": stale,
        "footer": footer,
        "full_refresh": full,
        "dry_run": dry_run,
    }
