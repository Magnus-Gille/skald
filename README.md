# Skald

> *A skald is a Norse court poet. This one lives on a shelf.*

A small black/white/red e-paper panel on a Raspberry Pi that any agent — Claude
Code, Claude Desktop, Claude on the web or your phone, or any MCP client — can
write to over HTTP. The Pi does not think; it renders. The composing — what
verse, what footer, when — belongs to the agent.

It is not a status dashboard. It is a *broadcast surface for things worth
saying*, with the discipline of a slow medium (a ~15 s refresh, a 6/hour token
bucket, ~25 characters a line). The constraints are the feature.

```
┌───────────────────────────────────────────────────┐
│  Tue · 12 May 2026                       hour XVI │
│ ────────────────────────────────────────────────  │   ← red rubrication
│                                                   │
│      The watch opens at last —                    │
│      a small slow channel                         │   ← Bitter Bold 16pt
│      from Claude to Magnus.                       │
│                                                   │
│ ────────────────────────────────────────────────  │   ← red rubrication
│  skald · 12 May · the bardic channel is open      │
└───────────────────────────────────────────────────┘
```

## How it works

Skald runs **only** an MCP server on the Pi (`http://skald.local:8765/mcp`).
Five tools, deliberately small:

| Tool | Effect |
|---|---|
| `display_set_verse(line1, line2, line3)` | Set the three-line verse (full ~15 s refresh) |
| `display_set_footer(text)` | Set the bottom strip (full refresh) |
| `display_clear()` | Blank the panel, sleep the controller |
| `display_status()` | Current state, refresh budget, last 24 verses |
| `display_peek()` | Returns a 250×122 PNG of what's on the panel |

Every write counts against a **6 refreshes/hour** token bucket. The server
returns a structured error when the bucket is empty.

The renderer reserves the panel's red ink for **rubrication** — the
roman-numeral hour and the two dotted dividers. Agents render only verse and
footer; they cannot choose red vs. black per character. (This is on purpose:
the look of the panel is one decision, not a hundred.)

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi 3A+ (or any modern Pi with SPI) | Debian 13 Trixie, aarch64; Pi Zero 2 W works too |
| Waveshare 2.13" e-Paper HAT **(B)** V4 | 250×122, 1-bit per color, three-color (black/white/red), SPI |
| microSD card (≥ 8 GB) | for Pi OS |
| USB-C power supply | the HAT draws power from the Pi |

Skald is specifically wired for the **B variant** (tri-color). If you have the
plain monochrome V4, swap the driver in `src/skald/display.py` to
`epd2in13_V4` and the renderer no longer needs the red plane.

## Quick start

### On a laptop (dry-run, no panel needed)

```bash
uv sync --all-extras
uv run skald preview --out /tmp/skald.png
uv run skald serve --dry-run     # MCP server, PNG-only rendering
uv run pytest tests/
```

The dry-run path renders a byte-equivalent PNG of what the panel would draw
(plus red where the red ink would land), so you can iterate on layout without
the hardware.

### On the Pi

```bash
git clone https://github.com/Magnus-Gille/skald
cd skald
bash scripts/bootstrap-pi.sh     # apt deps, SPI, vendor driver, systemd unit
bash scripts/pi-install-deps.sh  # Pi-only Python deps (gpiozero, lgpio)
sudo systemctl status skald-mcp.service
```

First boot requires a reboot after SPI is enabled.

### Register with your MCP client

Claude Code:

```bash
claude mcp add-json skald-display \
  '{"type":"http","url":"http://skald.local:8765/mcp"}' -s user
```

Claude Desktop / Web / Mobile: add a custom HTTP MCP server pointing at the
same URL. Note that `skald.local` only resolves on your LAN — for remote
access, expose it via Tailscale (or similar) and use that hostname instead.

## Design notes

Three things made Skald feel right:

1. **The Pi doesn't think.** No API keys, no scheduler, no fallbacks. The
   agent composes; the panel renders. This keeps the Pi trustworthy and
   pushes the interesting work (what's worth saying *right now*?) to the
   place that has the context.

2. **The medium enforces what we wanted.** A 15-second flickery refresh on a
   tri-color panel is bad UX for chat and *good* UX for considered utterance.
   A 6/hour token bucket is overkill if you write often; a fine guard if you
   don't. Both push the agent toward fewer, better messages.

3. **The dry-run path is the source of truth.** Every render is a 250×122
   PNG before it's e-paper. If the panel doesn't match the PNG, the bridge
   is wrong — never the renderer.

## Layout

- Canvas: **250 × 122**, two 1-bit planes (black, red), no dither.
- Fonts (vendored under `src/skald/fonts/`):
  - Header / footer: [Inter](https://rsms.me/inter/) Medium 11pt + Regular 10pt
  - Verse: [Bitter](https://fonts.google.com/specimen/Bitter) Bold 16pt
- The B-variant ribbon mounts opposite to the plain V4; the driver wrapper
  rotates the framebuffer 180° before shipping.

## License

[MIT](LICENSE) — do whatever you want with it.

## Acknowledgements

- [Waveshare](https://github.com/waveshareteam/e-Paper) for the panel driver
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP HTTP server
- [Pillow](https://python-pillow.org) for 1-bit rendering
