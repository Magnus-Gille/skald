# Skald — Status

**Last session:** 2026-05-29
**Branch:** master
**Head:** d216ed0 (user-systemd migration; CLAUDE.md + STATUS.md doc update pending commit)

## Completed This Session

- **Migrated `skald-mcp` from system to user systemd service** (`refactor: run skald-mcp as user service`, `d216ed0`). Dropped `User=`/`Group=` from the unit, changed `WantedBy=multi-user.target` → `default.target`. `deploy.sh` and `bootstrap-pi.sh` now install to `~/.config/systemd/user/` and use `systemctl --user`; bootstrap also runs `loginctl enable-linger`.
- **Resolved the long-standing sudo-restart friction** (prior blocker #1). Restarts are now `systemctl --user restart skald-mcp` — no password, no TTY. This was the only high-severity entry in the friction log.
- **Deployed and verified on the Pi:** old system service disabled (`sudo systemctl disable --now`, one-time), new user service running, linger=yes (survives reboot), port 8765 listening, MCP healthy (406 to bare GET = correct).
- Updated CLAUDE.md "On the Pi" section to the sudo-free `--user` commands.

## In Progress / To Reconcile

- None. The prior "blocky PR / temp file-sync" reconciliation is resolved — `blocky` is merged (`fdb9f93`) and live.

## Blockers

- **Direct push to master is blocked** by the Claude Code auto-mode classifier in some sessions → deploys may need feature branch + PR. (This session pushed to master successfully.)

## Next Steps

1. Tailscale to expose `skald.local:8765` off-LAN.
2. Larger display options (Inky Impression 4", Waveshare 4.2").
