"""FastMCP HTTP server — five tools to drive Skald's display."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from PIL import Image

from . import layout
from .display import get_display
from .state import State


SERVER_INSTRUCTIONS = """\
Skald is a small e-paper panel (250×122, black/white/red) that lives on a
shelf. It is **not** a chat surface. Think of each call as engraving rather
than typing: every refresh takes ~15 seconds with a visible flicker, costs
panel wear, and is metered (6 refreshes/hour via a token bucket).

What to write:
- A short verse worth looking at — three lines, ~25 characters each.
- Footers should add a small grace note, not a status dump.
- Read `display_status` first; `recent_verses` shows the last 24 entries —
  don't repeat yourself.

What to avoid:
- Status dashboards, tickers, anything that changes every minute.
- Calling on a schedule "just because". Silence is fine; the panel holds
  the last image without power.
- Long content; lines that overflow ~25 chars get rejected.

Red ink on this panel is reserved by the renderer for rubrication
(the roman-numeral hour and the dividers) — agents render verse/footer
text only; they cannot choose red vs. black per character.
"""


def build_server(dry_run: bool = False, out_path: Optional[Path] = None) -> FastMCP:
    """Build (but do not start) the Skald MCP server."""
    mcp = FastMCP("skald", instructions=SERVER_INSTRUCTIONS)

    def _disp():
        return get_display(dry_run=dry_run, out_path=out_path)

    def _render_current(state: State):
        """Returns (black, red) planes."""
        return layout.render(verse=state.verse, footer=state.footer)

    @mcp.tool
    def display_set_verse(line1: str, line2: str, line3: str) -> dict:
        """Set the three-line verse — the heart of Skald's panel.

        Lines render in bold slab serif (Bitter Bold 16pt), centered.
        Width is the hard constraint, not character count: ~27 chars of
        normal English fits; wide letters (W, M) cap closer to ~14.
        The server measures actual pixel width and returns an error if
        any line overflows. Pass empty strings to blank a line.

        Triggers a slow tri-color refresh (~15 seconds, visible flicker)
        and counts 1 against the 6/hour token bucket. If the bucket is
        empty, returns `{"ok": false, "error": "..."}` without touching
        the panel. Always read `display_status` first to check the budget
        and avoid repeating yourself (see `recent_verses`).
        """
        state = State.load()
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        lines = [line1, line2, line3]
        too_wide = layout.measure_verse_overflow(lines)
        if too_wide:
            return {
                "ok": False,
                "error": (
                    "verse line too wide for the panel — keep each line to "
                    "~27 characters of normal English (less for wide letters "
                    f"like W/M). Overflow: {too_wide}"
                ),
            }
        state.verse = lines
        state.verse_source = "mcp"
        state.remember_verse(lines)
        black, red = layout.render(verse=lines, footer=state.footer)
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "verse": lines, "full_refresh": full}

    @mcp.tool
    def display_set_footer(text: str) -> dict:
        """Set the footer line (small strip under the bottom divider).

        At most **44 characters** in 10pt regular sans. The footer holds
        a single grace note — a place, a weather hint, a calendar peek,
        a date. Not a status dump.

        Triggers a slow tri-color refresh and counts 1 against the
        6/hour token bucket. Returns `{"ok": false, "error": "..."}` if
        the budget is empty.
        """
        state = State.load()
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        if len(text) > 44:
            return {"ok": False, "error": "footer must be at most 44 characters"}
        state.footer = text
        state.footer_source = "mcp"
        black, red = layout.render(verse=state.verse, footer=text)
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "footer": text, "full_refresh": full}

    @mcp.tool
    def display_clear() -> dict:
        """Blank the panel and put the controller to sleep.

        Triggers a full ~15s refresh and counts 1 against the 6/hour
        budget. Use sparingly — mainly before powering down or for
        deliberate maintenance. The panel holds the last image without
        power, so "clearing because nothing to say" is rarely needed —
        prefer to just leave the last verse up.
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
        """Read the current state without touching the panel — free, no budget cost.

        Always call this first before deciding to write. Returns:
        - `verse`, `footer`: what's currently on the panel.
        - `verse_source`, `footer_source`: "boot" (untouched) or "mcp" (an agent set it).
        - `last_full_refresh`, `last_partial_refresh`: unix timestamps.
        - `refresh_budget_remaining_this_hour`: refresh slots left (max 6).
        - `recent_verses`: the last 24 verses, newest first. Avoid repeating these.
        """
        state = State.load()
        used = state.effective_bucket_used()
        return {
            "verse": state.verse,
            "verse_source": state.verse_source,
            "footer": state.footer,
            "footer_source": state.footer_source,
            "last_full_refresh": state.last_full_refresh,
            "last_partial_refresh": state.last_partial_refresh,
            "partials_since_full": state.partials_since_full,
            "refresh_budget_used_this_hour": used,
            "refresh_budget_remaining_this_hour": max(0, 6 - used),
            "recent_verses": state.recent_verses,
        }

    @mcp.tool
    def display_peek() -> dict:
        """Return the current framebuffer as a base64-encoded RGB PNG (250×122).

        Composed view: black ink as black, red ink as red, bare panel as
        white. Lets any agent — Code, Desktop, Web, Mobile — *see* what
        the panel looks like right now without SSH or a camera.

        Free, no budget cost. Useful after `display_set_verse` to confirm
        what landed.
        """
        state = State.load()
        black, red = _render_current(state)
        # Compose to an RGB preview so the peek shows red where red ink would land.
        preview = Image.new("RGB", black.size, (255, 255, 255))
        bp, rp = black.load(), red.load()
        op = preview.load()
        for y in range(black.height):
            for x in range(black.width):
                if bp[x, y] == 0:
                    op[x, y] = (0, 0, 0)
                elif rp[x, y] == 0:
                    op[x, y] = (190, 40, 40)
        buf = io.BytesIO()
        preview.save(buf, format="PNG")
        return {
            "ok": True,
            "format": "image/png",
            "width": preview.width,
            "height": preview.height,
            "data_base64": base64.b64encode(buf.getvalue()).decode("ascii"),
        }

    return mcp
