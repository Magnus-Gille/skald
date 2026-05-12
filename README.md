# Skald

A small, slow voice on a 2.13" e-paper screen.

Skald is a Raspberry Pi 3A+ with a Waveshare 2.13" e-Paper HAT V4 (250×122, 1-bit).
Every hour it composes a short verse — three lines, freshly written by Claude Haiku —
and shows it on the panel, framed by a date header and a footer with outside weather.

Any agent (Claude Code, Desktop, Web, Mobile) can drive the display through an HTTP
MCP server running on the Pi.

## Quick start

```bash
uv sync
uv run skald preview --out /tmp/skald.png   # dry-run render to PNG
uv run skald serve --dry-run                 # run the MCP server locally
uv run skald tick --dry-run                  # compose + render once
```

## Hardware

- Raspberry Pi 3A+ (aarch64, Debian 13 trixie)
- Waveshare 2.13" e-Paper HAT V4 — 250×122, 1-bit, SPI

## Layout — "Skald's Watch"

```
┌───────────────────────────────────────────────────┐
│  Tue · 12 May 2026                       hour XI  │
│ ────────────────────────────────────────────────  │
│      Lunchtime light on the laptop keys,          │
│      a half-formed verse waits in the wood —      │
│      the e-ink learns to breathe.                 │
│ ────────────────────────────────────────────────  │
│  ◐ 14° clear         next: 14:00 Magnus / Anna    │
└───────────────────────────────────────────────────┘
```

## MCP tools

- `display_set_verse(line1, line2, line3)` — set the three-line verse (partial refresh).
- `display_set_footer(text)` — override the footer line (partial refresh).
- `display_clear()` — full refresh to blank, panel to sleep.
- `display_status()` — current state, last refresh times, refresh budget.
- `display_peek()` — base64 PNG of the current framebuffer.

## Layout

See the plan at `~/.claude/plans/starry-wondering-peacock.md`.
