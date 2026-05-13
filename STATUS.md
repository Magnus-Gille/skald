# Skald — Status

**Last session:** 2026-05-13
**Branch:** master (up to date with origin)

## Completed This Session

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

Nothing. All changes shipped and deployed.

## Blockers

- The auto-mode classifier blocks `git push origin master` on agent-driven
  pushes — Magnus must push manually each time (local commit → user pushes →
  `ssh skald && git pull && restart`). Considering a Makefile deploy target.

## Next Steps

1. **Watch the hourly hook in the wild** — adjust nudge text or throttle if it
   produces filler rather than meaningful verses.
2. **Makefile deploy target** — `make deploy` to replace the manual
   push + ssh + pull + restart sequence.
3. **Tailscale** — expose `skald.local:8765` for off-LAN (Desktop/Web/Mobile)
   agent access.
4. **Larger display** — Top picks from 2026-05-12 research:
   - Pimoroni Inky Impression 4" (7-color, 640×400) @ Botland
   - Waveshare 4.2" tri-color B/W/R (400×300) @ BerryBase
   - Waveshare 4.2" mono (400×300) @ BerryBase — cheapest, fastest refresh
