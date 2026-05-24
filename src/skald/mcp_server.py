"""FastMCP HTTP server — six tools to drive Skald's display."""

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
        return layout.render(
            verse=state.verse,
            footer=state.footer,
            style=state.font_style,
            avatar=state.load_avatar(),
        )

    def _resolve_style(style: Optional[str], state: State) -> tuple[str, Optional[str]]:
        """Return (effective_style, error_or_None)."""
        if style is None:
            return state.font_style, None
        if style not in layout.FONT_STYLES:
            valid = ", ".join(sorted(layout.FONT_STYLES))
            return state.font_style, f"unknown style '{style}'; valid options: {valid}"
        return style, None

    @mcp.tool
    def display_set_verse(line1: str, line2: str, line3: str, style: Optional[str] = None) -> dict:
        """Set the three-line verse — the heart of Skald's panel.

        Lines render centered in the chosen font style (default: "serif").
        Width is the hard constraint, not character count: the server
        measures actual pixel width and returns an error if any line
        overflows. Pass empty strings to blank a line.

        `style` selects the font preset: "serif" (Bitter Bold, default),
        "pixel" (HaxrCorp4089 + Born2bSportyV2), "sporty" (Born2bSportyV2),
        or "gravity" (GravityBold8). Omit to keep the current style.

        Triggers a slow tri-color refresh (~15 seconds, visible flicker)
        and counts 1 against the 6/hour token bucket. If the bucket is
        empty, returns `{"ok": false, "error": "..."}` without touching
        the panel. Always read `display_status` first to check the budget
        and avoid repeating yourself (see `recent_verses`).

        If you're also changing the footer, prefer `display_set_panel`
        instead — it updates both in a single refresh and costs one token.
        """
        state = State.load()
        effective_style, style_err = _resolve_style(style, state)
        if style_err:
            return {"ok": False, "error": style_err}
        lines = [line1, line2, line3]
        has_avatar = state.avatar_path is not None
        too_wide = layout.measure_verse_overflow(lines, effective_style, has_avatar)
        if too_wide:
            return {
                "ok": False,
                "error": (
                    "verse line too wide for the panel — keep each line to "
                    "~27 characters of normal English (less for wide letters "
                    f"like W/M). Overflow: {too_wide}"
                ),
            }
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        state.verse = lines
        state.verse_source = "mcp"
        state.font_style = effective_style
        state.remember_verse(lines)
        black, red = layout.render(
            verse=lines, footer=state.footer, style=effective_style,
            avatar=state.load_avatar(),
        )
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "verse": lines, "style": effective_style, "full_refresh": full}

    @mcp.tool
    def display_set_footer(text: str, style: Optional[str] = None) -> dict:
        """Set the footer line (small strip under the bottom divider).

        At most **44 characters** in the footer font of the current style.
        The footer holds a single grace note — a place, a weather hint,
        a calendar peek, a date. Not a status dump.

        `style` optionally changes the font preset for the whole panel:
        "serif" (default), "pixel", "sporty", or "gravity".

        Triggers a slow tri-color refresh and counts 1 against the
        6/hour token bucket. Returns `{"ok": false, "error": "..."}` if
        the budget is empty.

        If you're also changing the verse, prefer `display_set_panel`
        instead — it updates both in a single refresh and costs one token.
        """
        state = State.load()
        effective_style, style_err = _resolve_style(style, state)
        if style_err:
            return {"ok": False, "error": style_err}
        if len(text) > 44:
            return {"ok": False, "error": "footer must be at most 44 characters"}
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        state.footer = text
        state.footer_source = "mcp"
        state.font_style = effective_style
        black, red = layout.render(
            verse=state.verse, footer=text, style=effective_style,
            avatar=state.load_avatar(),
        )
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "footer": text, "style": effective_style, "full_refresh": full}

    @mcp.tool
    def display_set_panel(
        line1: Optional[str] = None,
        line2: Optional[str] = None,
        line3: Optional[str] = None,
        footer: Optional[str] = None,
        style: Optional[str] = None,
    ) -> dict:
        """Update verse and/or footer atomically — one refresh, one token.

        Use this when you'd otherwise call `display_set_verse` and
        `display_set_footer` back-to-back: those would trigger two
        separate ~15-second panel refreshes and spend two bucket tokens
        for what is conceptually a single moment. This tool composes the
        framebuffer once, refreshes the panel once, and bills one token.

        Arguments are all optional, with two rules:
          - The verse is updated as a unit: provide all three lines or
            none. Pass `""` to blank a line.
          - At least one of (verse, footer, style) must be provided.

        `style` selects the font preset for the whole panel:
          - "serif" — Bitter Bold 16pt verse, Inter header/footer (default)
          - "pixel" — HaxrCorp4089 verse, helvb08 header, Born2bSportyV2 footer
          - "sporty" — Born2bSportyV2 verse and header, helvb08 footer
          - "gravity" — GravityBold8 verse, helvb08 header/footer

        Same width/length constraints as the single-field tools:
        verse lines must fit the panel pixel-width (measured using the chosen
        font); footer ≤ 44 chars. Validation runs before the token is
        consumed, so a malformed call does not cost a refresh slot.
        """
        state = State.load()

        effective_style, style_err = _resolve_style(style, state)
        if style_err:
            return {"ok": False, "error": style_err}

        verse_lines = (line1, line2, line3)
        verse_provided_count = sum(v is not None for v in verse_lines)
        if 0 < verse_provided_count < 3:
            return {
                "ok": False,
                "error": (
                    "verse is updated as a unit — provide all three "
                    "lines together (pass empty strings to blank a line) "
                    "or omit them all to leave the verse unchanged"
                ),
            }
        verse_provided = verse_provided_count == 3
        footer_provided = footer is not None
        style_changed = style is not None and effective_style != state.font_style

        if not verse_provided and not footer_provided and not style_changed:
            return {
                "ok": False,
                "error": "nothing to update — provide verse (all 3 lines), footer, and/or style",
            }

        if verse_provided:
            lines = [line1, line2, line3]
            has_avatar = state.avatar_path is not None
            too_wide = layout.measure_verse_overflow(lines, effective_style, has_avatar)
            if too_wide:
                return {
                    "ok": False,
                    "error": (
                        "verse line too wide for the panel — keep each line to "
                        "~27 characters of normal English (less for wide letters "
                        f"like W/M). Overflow: {too_wide}"
                    ),
                }
        if footer_provided and len(footer) > 44:
            return {"ok": False, "error": "footer must be at most 44 characters"}

        err = state.take_token()
        if err:
            return {"ok": False, "error": err}

        if verse_provided:
            state.verse = lines
            state.verse_source = "mcp"
            state.remember_verse(lines)
        if footer_provided:
            state.footer = footer
            state.footer_source = "mcp"
        state.font_style = effective_style

        black, red = layout.render(
            verse=state.verse, footer=state.footer, style=effective_style,
            avatar=state.load_avatar(),
        )
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()

        result: dict = {"ok": True, "style": effective_style, "full_refresh": full}
        if verse_provided:
            result["verse"] = state.verse
        if footer_provided:
            result["footer"] = state.footer
        return result

    @mcp.tool
    def display_set_avatar(data_base64: str) -> dict:
        """Upload a 1-bit avatar image for the left column of the panel.

        The avatar occupies the leftmost 50×122 px of the display. All
        text content (header, verse, footer) shifts into the remaining
        200×122 px right column, separated by a dotted red vertical line.

        `data_base64`: base64-encoded PNG (or any PIL-readable format).
        Any size and mode is accepted — the image is converted to 1-bit
        and scaled to exactly 50×122 px. Costs one refresh token.

        To remove the avatar and return to the full-width layout, call
        `display_clear_avatar`.
        """
        import base64, io
        state = State.load()
        try:
            raw = base64.b64decode(data_base64)
            img = Image.open(io.BytesIO(raw))
        except Exception as e:
            return {"ok": False, "error": f"could not decode image: {e}"}
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        save_path = state.avatar_save_path()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.convert("1").resize((layout.AVATAR_W, layout.CANVAS_H), Image.LANCZOS).save(save_path)
        state.avatar_path = str(save_path)
        black, red = layout.render(
            verse=state.verse, footer=state.footer, style=state.font_style,
            avatar=state.load_avatar(),
        )
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "avatar_size_px": f"{layout.AVATAR_W}×{layout.CANVAS_H}", "full_refresh": full}

    @mcp.tool
    def display_clear_avatar() -> dict:
        """Remove the avatar and return to the full-width text layout.

        Costs one refresh token.
        """
        state = State.load()
        if not state.avatar_path:
            return {"ok": True, "note": "no avatar was set"}
        err = state.take_token()
        if err:
            return {"ok": False, "error": err}
        try:
            Path(state.avatar_path).unlink(missing_ok=True)
        except OSError:
            pass
        state.avatar_path = None
        black, red = layout.render(verse=state.verse, footer=state.footer, style=state.font_style)
        full = state.needs_full_refresh()
        _disp().show(black, red, partial=not full)
        state.record_refresh(partial=not full)
        state.save()
        return {"ok": True, "full_refresh": full}

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
            "font_style": state.font_style,
            "available_styles": list(layout.FONT_STYLES.keys()),
            "avatar": "set" if state.avatar_path else "none",
            "avatar_size_px": f"{layout.AVATAR_W}×{layout.CANVAS_H}" if state.avatar_path else None,
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
