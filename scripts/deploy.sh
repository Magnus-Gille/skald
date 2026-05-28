#!/usr/bin/env bash
# Run on the laptop. Syncs the repo to skald, restarts services.
set -euo pipefail

HOST="${SKALD_HOST:-skald}"
REMOTE="${SKALD_REMOTE:-/home/magnus/repos/skald}"

cd "$(dirname "$0")/.."

echo "==> rsync to $HOST:$REMOTE"
rsync -az --delete \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '.pytest_cache' \
    --exclude 'tests/golden' \
    --exclude 'src/skald/vendor' \
    ./ "$HOST:$REMOTE/"

echo "==> install / restart on $HOST"
ssh "$HOST" bash <<EOF
set -euo pipefail
cd $REMOTE
if [ ! -d .venv ]; then
    bash scripts/bootstrap-pi.sh
else
    .venv/bin/pip install -e .[pi] --quiet
    mkdir -p ~/.config/systemd/user
    install -m 0644 deploy/skald-mcp.service ~/.config/systemd/user/skald-mcp.service
    systemctl --user daemon-reload
    systemctl --user enable skald-mcp.service
    systemctl --user restart skald-mcp.service
fi
systemctl --user status skald-mcp.service --no-pager -l | head -20
EOF

echo "==> deploy complete"
