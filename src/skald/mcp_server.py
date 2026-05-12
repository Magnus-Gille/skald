"""FastMCP HTTP server — five tools to drive Skald's display."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from . import layout
from .display import get_display
from .state import State


def build_server(dry_run: bool = False, out_path: Optional[Path] = None) -> FastMCP:
    """Build (but do not start) the Skald MCP server."""
    mcp = FastMCP("skald")

    def _disp():
        return get_display(dry_run=dry_run, out_path=out_path)

    def _render_current(state: State):
        return layout.render(verse=state.verse, footer=state.footer)

    @mcp.tool
    def display_set_verse(line1: str, line2: str, line3: str) -> dict:
        """Set the three-line verse shown on Skald's display.

        Each line should be at most ~30 characters. The verse is pushed
        immediately via partial refresh (a full refresh is occasionally
        forced to prevent panel ghosting). Counts against the hourly
        refresh budget (6/hour for MCP-triggered refreshes).
        """
        state = State.load()
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        lines = [line1, line2, line3]
        if any(len(line) > 36 for line in lines):
            return {"ok": False, "error": "each line must be at most 36 characters"}
        state.verse = lines
        state.verse_source = "mcp"
        state.verse_stale = False
        state.remember_verse(lines)
        img = layout.render(verse=lines, footer=state.footer)
        full = state.needs_full_refresh()
        _disp().show(img, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "verse": lines, "full_refresh": full}

    @mcp.tool
    def display_set_footer(text: str) -> dict:
        """Override the footer line (the small bottom strip).

        Use this to surface a one-off note, a small joke, weather, or
        anything else that fits in ~44 characters.
        """
        state = State.load()
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        if len(text) > 44:
            return {"ok": False, "error": "footer must be at most 44 characters"}
        state.footer = text
        state.footer_source = "mcp"
        img = layout.render(verse=state.verse, footer=text)
        full = state.needs_full_refresh()
        _disp().show(img, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "footer": text, "full_refresh": full}

    @mcp.tool
    def display_clear() -> dict:
        """Clear the panel to blank white and put it to sleep.

        Forces a full refresh. Use sparingly — primarily before powering
        down or for maintenance.
        """
        state = State.load()
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        _disp().clear()
        state.verse = ["", "", ""]
        state.footer = ""
        state.record_refresh(partial=False)
        state.save()
        return {"ok": True}

    @mcp.tool
    def display_status() -> dict:
        """Return what is currently shown plus refresh stats and recent verses.

        `recent_verses` is the last ~24 verses shown — use this to avoid
        repeating yourself when composing a new one.
        """
        state = State.load()
        return {
            "verse": state.verse,
            "verse_source": state.verse_source,
            "footer": state.footer,
            "footer_source": state.footer_source,
            "last_full_refresh": state.last_full_refresh,
            "last_partial_refresh": state.last_partial_refresh,
            "partials_since_full": state.partials_since_full,
            "refresh_budget_used_this_hour": state.bucket_used,
            "refresh_budget_remaining_this_hour": max(0, 6 - state.bucket_used),
            "recent_verses": state.recent_verses,
        }

    @mcp.tool
    def display_peek() -> dict:
        """Return the current framebuffer as a base64-encoded PNG.

        This is what the panel is currently showing (or would show, in
        dry-run mode). Useful for debugging the display from any agent
        without SSH.
        """
        state = State.load()
        img = _render_current(state)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return {
            "ok": True,
            "format": "image/png",
            "width": img.width,
            "height": img.height,
            "data_base64": base64.b64encode(buf.getvalue()).decode("ascii"),
        }

    return mcp
