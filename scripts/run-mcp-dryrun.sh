#!/usr/bin/env bash
# Run the Skald MCP server in dry-run mode (no hardware), detached.
# This is a stop-gap until SPI + systemd are set up on the Pi.
set -euo pipefail
REPO="${REPO:-/home/magnus/repos/skald}"
SHARE="$HOME/.local/share/skald"
mkdir -p "$SHARE"

# stop previous
pkill -f "skald serve" || true
sleep 1

export SKALD_FORCE_DRYRUN=1
export SKALD_STATE_PATH="$SHARE/state.json"
export SKALD_PREVIEW_PATH="$SHARE/current.png"

cd "$REPO"
nohup ./.venv/bin/python -m skald serve --dry-run \
    --host 0.0.0.0 --port 8765 --path /mcp \
    >> "$SHARE/serve.log" 2>&1 </dev/null &
echo $! > "$SHARE/serve.pid"
disown || true
echo "started pid=$(cat "$SHARE/serve.pid")"
