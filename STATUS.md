# Skald — Status

**Last session:** 2026-05-22
**Branch:** master

## Completed This Session

- Designed a minimal display-native lofi cassette mark for the 2.13" B/W/R panel:
  - `assets/lofi-avatar-preview.png` — composed RGB preview at exactly
    250×122 (`30,500` panel pixels)
  - `assets/lofi-avatar-black.png` — 1-bit black plane
  - `assets/lofi-avatar-red.png` — 1-bit red plane
  - Ink bounding box is `x=7..47`, `y=29..89`, so it fits in the left fifth
    of the 250px-wide display.
  - Current ink counts: 906 black pixels and 401 red pixels.
- Added `scripts/render_lofi_avatar.py` as the source renderer for the asset.
  It draws directly on separate 1-bit planes and clears red where black ink is
  present, matching the display compositor's black-over-red priority.
- Added `tests/test_lofi_avatar.py` to guard canvas size, mode, red/black use,
  no plane overlap, and left-fifth placement.
- Verification: `uv run pytest` passes (`9 passed`);
  `uv run ruff check scripts/render_lofi_avatar.py tests/test_lofi_avatar.py`
  passes.

## Previous Session

- `842c9fd` — fix: `display_status` was reporting stale bucket state after
  window expiry. Added `State.effective_bucket_used()` so the reported
  remaining tokens reflect the post-expiry reset without requiring a write.
- `9b8aedc` — feat: `display_set_panel(line1?, line2?, line3?, footer?)` —
  atomic verse+footer update, one render, one refresh, one token. Solves the
  double-flicker problem when writing both fields together.
- Laptop hourly hook: `~/.claude/hooks/skald-nudge.sh` registered in
  `~/.claude/settings.json` as a synchronous UserPromptSubmit hook. Fires
  once per hour when Magnus is actively using Claude; injects a nudge asking
  Claude to consider writing a contextual verse. Escape hatch:
  `touch ~/.local/state/skald/nudge-disabled`.
- Pi repo converted from rsync-only to proper git checkout (tracking on
  `origin/master`). Future deploys: `git pull && sudo systemctl restart skald-mcp.service`.
- First contextual verse this session: "The channel had no clock. / Now it
  learns the hour. / Silence between bells."
- CLAUDE.md updated to document `display_set_panel` and correct tool count.

## In Progress

Nothing. Avatar asset is generated and tested locally; not committed or
deployed.

## Blockers

- The auto-mode classifier blocks `git push origin master` on agent-driven
  pushes — Magnus must push manually each time (local commit → user pushes →
  `ssh skald && git pull && restart`). Considering a Makefile deploy target.

## Next Steps

1. **Watch the hourly hook in the wild** — adjust nudge text or throttle if it
   produces filler rather than meaningful verses.
2. **Decide how to expose image assets over MCP** if the avatar should be
   displayed on hardware rather than kept as a repo asset. Current MCP tools
   only expose text/verse rendering, not arbitrary bitmap display.
3. **Makefile deploy target** — `make deploy` to replace the manual
   push + ssh + pull + restart sequence.
4. **Tailscale** — expose `skald.local:8765` for off-LAN (Desktop/Web/Mobile)
   agent access.
5. **Larger display** — Top picks from 2026-05-12 research:
   - Pimoroni Inky Impression 4" (7-color, 640×400) @ Botland
   - Waveshare 4.2" tri-color B/W/R (400×300) @ BerryBase
   - Waveshare 4.2" mono (400×300) @ BerryBase — cheapest, fastest refresh
