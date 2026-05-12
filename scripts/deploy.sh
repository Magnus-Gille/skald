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
    sudo install -m 0644 deploy/skald-mcp.service  /etc/systemd/system/skald-mcp.service
    sudo install -m 0644 deploy/skald-tick.service /etc/systemd/system/skald-tick.service
    sudo install -m 0644 deploy/skald-tick.timer   /etc/systemd/system/skald-tick.timer
    sudo systemctl daemon-reload
    sudo systemctl restart skald-mcp.service
fi
systemctl status skald-mcp.service --no-pager -l | head -20
EOF

echo "==> deploy complete"
