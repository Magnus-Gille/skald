# Skald

A 2.13" e-paper screen on a Raspberry Pi 3A+ that any agent can write to over MCP.

Skald itself does not think. It listens on `http://skald.local:8765/mcp` and renders
whatever the agent says to render. The composing — what verse, what footer, when —
lives with the agent. Magnus built skald so Claude has a small slow channel to him.

## MCP tools

- `display_set_verse(line1, line2, line3)` — set the three-line verse (partial refresh).
- `display_set_footer(text)` — set the footer line (partial refresh).
- `display_clear()` — full refresh to blank, panel sleep.
- `display_status()` — current verse/footer, refresh stats, recent history.
- `display_peek()` — base64 PNG of the current framebuffer.

All five count against a 6/hour token bucket to prevent burning the panel.

## Layout — 250×122 1-bit

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

## Develop without hardware

```bash
uv sync
uv run skald preview --out /tmp/skald.png
uv run skald serve --dry-run     # MCP server, PNG-only rendering
uv run pytest tests/
```

## Deploy to the Pi

```bash
./scripts/deploy.sh               # rsync to skald
ssh skald 'bash /home/magnus/repos/skald/scripts/bootstrap-pi.sh'
# First time: enables SPI, installs systemd unit, requires one reboot
```

## Register with Claude Code

```bash
claude mcp add-json skald-display '{"type":"http","url":"http://skald.local:8765/mcp"}' -s user
```

## Hardware

- Raspberry Pi 3A+ (aarch64, Debian 13 trixie)
- Waveshare 2.13" e-Paper HAT V4 — 250×122, 1-bit, SPI
