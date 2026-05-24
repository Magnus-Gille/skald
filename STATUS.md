# Skald — Status

**Last session:** 2026-05-24
**Branch:** master
**Head:** c78fdfb

## Completed This Session

- **Font styles** (`c78fdfb`): four named presets (serif/pixel/sporty/gravity) selectable via `style` param on all write tools; style persists in state. Vendored four Flipper Zero TTFs: HaxrCorp4089, Born2bSportyV2, helvb08, GravityBold8.
- **Two-column avatar layout**: left 50×122 px column for avatar image; all text shifts into right 200px column with dotted red vertical separator. Verse max-width validation accounts for narrower column.
- **New MCP tools**: `display_set_avatar(data_base64)` and `display_clear_avatar()`. Both deployed to Pi via rsync + manual service restart.
- **Skull avatar live on panel**: generated in PIL drawing code (no external image), uploaded via direct fastmcp HTTP client call (session MCP client had stale tool list from before restart).
- CLAUDE.md updated: new tools, font style table, avatar layout section.

## Untracked (Codex session — review separately)

A parallel Codex session produced:
- `AGENTS.md` — Codex-flavored project instructions
- `assets/lofi-avatar-{black,red,preview}.png` — cassette-tape avatar asset
- `scripts/render_lofi_avatar.py` — PIL renderer for the cassette asset
- `tests/test_lofi_avatar.py` — guards for canvas size, plane overlap, placement

These are not committed. The lofi cassette is a better long-term avatar than the skull — consider deploying it once reviewed.

## Blockers

- **Session MCP client doesn't reload after Pi service restart** — new tools added mid-session are invisible to the cached tool list; must call them via direct `fastmcp.Client` HTTP call. Workaround works fine.
- **Sudo password needed for service restart** — Magnus must run `ssh skald "sudo systemctl restart skald-mcp.service"` manually after each deploy. A Makefile deploy target or sudoers entry for this one command would remove the friction.

## Next Steps

1. **Review and commit the Codex lofi cassette avatar** — upload to panel via `display_set_avatar`, replacing the skull.
2. **Makefile deploy target** — `make deploy` = rsync + remote restart (with sudoers rule for the restart command).
3. **Tailscale** — expose `skald.local:8765` for off-LAN (Desktop/Web/Mobile) agent access.
4. **Larger display** — top picks from 2026-05-12 research:
   - Pimoroni Inky Impression 4" (7-color, 640×400) @ Botland
   - Waveshare 4.2" tri-color B/W/R (400×300) @ BerryBase
   - Waveshare 4.2" mono (400×300) @ BerryBase — cheapest, fastest refresh
5. **Watch hourly hook** — adjust nudge text or throttle if it produces filler.
