# Skald — project-local instructions

A small e-paper display: Raspberry Pi 3A+ (host `skald`) + Waveshare 2.13" V4 panel (250×122, 1-bit). Skald is a **broadcast surface** that any agent — primarily Claude — writes to over an HTTP MCP. The Pi does not think; it renders.

## Architecture

- **The Pi runs only the MCP server**, nothing else. No scheduled tasks, no composer, no API keys. Just `skald-mcp.service` listening on `http://skald.local:8765/mcp`.
- **Decisions live with the agent.** When Claude wants to show something, Claude composes the verse (or footer, or whatever) and calls `display_set_verse` / `display_set_footer`. Cadence is the agent's choice — ad-hoc, scheduled, prompted, doesn't matter.

## MCP tools

- `display_set_panel(line1?, line2?, line3?, footer?, style?)` — **preferred** for combined updates: sets verse and/or footer in one render, one refresh, one token. Validation runs before the token is consumed.
- `display_set_verse(line1, line2, line3, style?)` — set the three-line verse only (partial refresh).
- `display_set_footer(text, style?)` — set the footer line only (partial refresh).
- `display_set_avatar(data_base64)` — upload a 1-bit avatar into the left 50×122 px column; all text shifts into the right 200px column. Accepts any PIL-readable image, auto-scaled.
- `display_clear_avatar()` — remove the avatar and return to full-width text layout.
- `display_clear()` — full refresh to blank, panel sleep.
- `display_status()` — current verse/footer/style/avatar, refresh stats, recent history.
- `display_peek()` — base64 PNG of the current framebuffer.

All except `display_status` and `display_peek` count against a 6/hour token bucket to avoid agents burning the panel.

## Font styles

Pass `style` to any write tool. Style persists in state until changed.

| Style | Verse font | Header | Footer |
|---|---|---|---|
| `serif` | Bitter Bold 16pt (default) | Inter Medium 11pt | Inter Regular 10pt |
| `pixel` | HaxrCorp4089 20pt | helvb08 10pt | Born2bSportyV2 10pt |
| `sporty` | Born2bSportyV2 15pt | Born2bSportyV2 10pt | helvb08 10pt |
| `gravity` | GravityBold8 16pt (all-caps) | helvb08 10pt | helvb08 10pt |
| `blocky` | Born2bSportyV2, auto-fit | — (none) | — (none) |
| `board` | GravityBold8, auto-sized | — (none) | — (none) |

`blocky` is **pure centered text**, no header/footer/avatar/dividers. The font
size is **auto-fit**: `render_plain()` picks the largest size that fits every
line within the panel width *and* gives each line an even vertical band — so 3
short lines render big, while 4–5 longer lines shrink just enough to fill. There
is therefore no width limit to overflow (validation is a no-op for this style).
More than three rows are supported by splitting on `\n` inside the three MCP
verse fields. Footer/avatar in state are ignored while active.

`board` is the **airport split-flap** layout, structurally different from the
others: the verse lines become rows of black flap tiles with white reverse-video
letters and a thin red seam across each tile. **No header, no footer, no avatar**
— just the grid. Empty verse lines are dropped (no blank rows). Validation is by
column count, not pixel width: each row must be ≤ 16 characters (longer rows would
be truncated). Footer/avatar set in state are ignored while `board` is active and
return when you switch back to another style.

## Avatar layout

When an avatar is set, the panel splits into two columns:
- **Left 50×122 px**: avatar image (any source, scaled to fill)
- **Dotted red vertical separator** at x=50
- **Right 200×122 px**: header, verse (centered in right column), footer

Verse max width narrows from 238px to ~192px when avatar is active — lines must be a bit shorter. The MCP server measures and rejects overflows before spending a token.

## Conventions

- Python ≥ 3.11, managed by `uv`. Source in `src/skald/`.
- Entrypoints via `python -m skald {preview,serve,status}` or the `skald` script.
- Display canvas is **always** 250×122, mode `"1"` (1-bit), no dithering. The dry-run PNG is byte-equivalent to the panel framebuffer.
- Every hardware render wraps `epd.init() / draw / epd.sleep()`. Non-negotiable per Waveshare guidance.
- Force a full refresh every 12 partials or every 6 hours to prevent ghosting.
- Fonts live in `src/skald/fonts/` and are vendored.

## On the laptop (dry-run loop)

```bash
uv run skald preview --out /tmp/skald-preview.png
# Read the PNG back in-session to judge the look.
```

## On the Pi

`skald-mcp` runs as a **user** systemd service (`~/.config/systemd/user/`),
so no sudo is needed to inspect or restart it. Linger is enabled, so it
starts at boot without a login.

```bash
ssh skald
systemctl --user status skald-mcp.service
systemctl --user restart skald-mcp.service   # no sudo
journalctl --user -u skald-mcp.service -f
```

## Munin namespace

`projects/skald/status` — phase, current work, recent decisions. Update at session end if anything changed.

## What Skald is

A surface for the agent to be quiet on. Not a status dashboard. Not an autonomous voice. A small slow channel from Claude to Magnus, opened only when there's something worth saying.
