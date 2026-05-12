# Skald — project-local instructions

A small e-paper display: Raspberry Pi 3A+ (host `skald`) + Waveshare 2.13" V4 panel (250×122, 1-bit). Skald is a **broadcast surface** that any agent — primarily Claude — writes to over an HTTP MCP. The Pi does not think; it renders.

## Architecture

- **The Pi runs only the MCP server**, nothing else. No scheduled tasks, no composer, no API keys. Just `skald-mcp.service` listening on `http://skald.local:8765/mcp`.
- **Decisions live with the agent.** When Claude wants to show something, Claude composes the verse (or footer, or whatever) and calls `display_set_verse` / `display_set_footer`. Cadence is the agent's choice — ad-hoc, scheduled, prompted, doesn't matter.

## MCP tools

- `display_set_verse(line1, line2, line3)` — set the three-line verse (partial refresh).
- `display_set_footer(text)` — set the footer line (partial refresh).
- `display_clear()` — full refresh to blank, panel sleep.
- `display_status()` — current verse/footer, refresh stats, recent history.
- `display_peek()` — base64 PNG of the current framebuffer.

All five count against a 6/hour token bucket to avoid agents burning the panel.

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

```bash
ssh skald
systemctl status skald-mcp.service
sudo journalctl -u skald-mcp.service -f
```

## Munin namespace

`projects/skald/status` — phase, current work, recent decisions. Update at session end if anything changed.

## What Skald is

A surface for the agent to be quiet on. Not a status dashboard. Not an autonomous voice. A small slow channel from Claude to Magnus, opened only when there's something worth saying.
