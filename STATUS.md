# Skald — Status

**Last session:** 2026-05-28
**Branch:** master
**Head:** 0cb47d6 (+ uncommitted `blocky` style → PR pending)

## Completed This Session

- **Airport split-flap board** (`render_board`) + made it a selectable style `board`. Merged to master via PR #1 (`0cb47d6`). Flap tiles, white reverse-video letters, red seam; no header/footer/avatar; ≤16 chars/row.
- **New `blocky` style** — pure centered text, no header/footer/avatar/dividers. Font Born2bSportyV2. `render_plain()` **auto-fits** the font size to fill the panel (3 short lines → big; 4–5 longer lines → shrinks to fit). >3 rows supported via `\n` in the three MCP verse fields. Validation is a no-op for this style (auto-fit can't overflow). Docs updated (CLAUDE.md table + note, MCP docstrings). **Committed locally + pushed to a branch; PR open — NOT yet merged.**
- Iterated font choice live on hardware: helvb08 → haxrcorp4089 (too thin/hard to read) → Born2bSportyV2 (blocky + legible). Auto-fit resolved the "bigger vs more words vs more lines" tension.
- Pi worktree was cleaned earlier (reset to origin/master); render_board deployed via PR→pull→restart.

## In Progress / To Reconcile

- **Pi `layout.py` is a temporary file-sync** of the `blocky` work (uncommitted on the Pi). Once the `blocky` PR merges: `ssh skald 'cd ~/repos/skald && git stash && git pull && sudo systemctl restart skald-mcp.service'` to replace the temp file with the merged code. (The stash drops the redundant temp edits.)
- Live panel currently shows a 5-line `blocky` test verse.

## Blockers

- **Sudo password needed for service restart** — every deploy needs `ssh skald "sudo systemctl restart skald-mcp.service"` run manually by Magnus. A sudoers rule for that one command would let deploys be fully automated. (Hit repeatedly this session — each style tweak = one manual restart.)
- **Direct push to master is blocked** by the Claude Code auto-mode classifier → all deploys go via feature branch + PR.

## Next Steps

1. **Merge the `blocky` PR**, then pull+restart on the Pi to drop the temp file-sync.
2. **Sudoers rule** for `systemctl restart skald-mcp.service` (or a `make deploy` target) to end the manual-restart friction.
3. Tailscale to expose `skald.local:8765` off-LAN.
4. Larger display options (Inky Impression 4", Waveshare 4.2").
