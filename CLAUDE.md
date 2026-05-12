# Skald — project-local instructions

A delightful e-paper display: Raspberry Pi 3A+ (host `skald`) + Waveshare 2.13" V4 panel (250×122, 1-bit). The display shows a freshly-composed three-line verse every hour ("Skald's Watch"), and exposes an HTTP MCP for any agent to override the verse or footer.

## Conventions

- Python ≥ 3.11, managed by `uv`. Source in `src/skald/`.
- Entrypoints via `python -m skald {preview,tick,serve}` or the `skald` script.
- Display canvas is **always** 250×122, mode `"1"` (1-bit), no dithering. The dry-run PNG is byte-equivalent to the panel framebuffer.
- Every hardware render wraps `epd.init() / draw / epd.sleep()`. Non-negotiable per Waveshare guidance.
- Token bucket in `state.py` caps MCP-triggered refreshes to 6/hour. Force a full refresh every 12 partials or every 6 hours.
- Fonts live in `src/skald/fonts/` and are vendored — do not depend on system fonts on the Pi.
- The Anthropic API key lives in `/etc/skald/skald.env` on the Pi (root:magnus, 0640). Never commit it.

## On the laptop (dry-run loop)

```bash
uv run skald preview --out /tmp/skald-preview.png
# Read the PNG back in-session to judge the look.
```

## On the Pi

```
ssh skald
systemctl status skald-mcp.service skald-tick.timer
sudo journalctl -u skald-mcp.service -f
```

## Munin namespace

`projects/skald/status` — phase, current work, recent decisions. Update at session end if anything changed.

## What Skald is NOT

Not a status dashboard. Magnus has Hugin/Munin/Heimdall for that. Skald is a small, slow voice. It's allowed to be quiet.
