#!/usr/bin/env bash
# Run from laptop. Copies a remote-cleanup script to skald and executes it.
# Removes stale tick units, sparse-clones just the Waveshare Python lib, starts service.
set -euo pipefail

REMOTE_SCRIPT=$(cat <<'REMOTE'
#!/usr/bin/env bash
set -uo pipefail

echo "==> remove stale skald-tick units"
sudo systemctl disable --now skald-tick.timer skald-tick.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/skald-tick.service /etc/systemd/system/skald-tick.timer
sudo systemctl daemon-reload

echo "==> stop dry-run MCP if running"
pkill -f "skald serve" 2>/dev/null || true
sleep 1

echo "==> free leftover clones from previous failed runs"
rm -rf /tmp/e-Paper /home/magnus/e-Paper-src
df -h /home /tmp | tail -2

echo "==> sparse-clone Waveshare Python lib only (~1 MB)"
mkdir -p /home/magnus/e-Paper-src
cd /home/magnus/e-Paper-src
git init -q
git remote add origin https://github.com/waveshareteam/e-Paper 2>/dev/null || true
git config core.sparseCheckout true
echo "RaspberryPi_JetsonNano/python/lib/waveshare_epd/*" > .git/info/sparse-checkout
DEFAULT_BRANCH=$(git ls-remote --symref origin HEAD 2>/dev/null | awk '/^ref:/ {sub("refs/heads/", "", $2); print $2; exit}')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-master}
echo "    fetching branch: $DEFAULT_BRANCH"
git fetch --depth 1 origin "$DEFAULT_BRANCH" 2>&1 | tail -3
git checkout FETCH_HEAD -- RaspberryPi_JetsonNano/python/lib/waveshare_epd
echo "    files pulled:"
ls RaspberryPi_JetsonNano/python/lib/waveshare_epd | head -5
echo "    epd2in13_V4.py size:"
wc -l RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd2in13_V4.py

echo "==> install into project vendor dir"
sudo rm -rf /home/magnus/repos/skald/src/skald/vendor/waveshare_epd
cp -r /home/magnus/e-Paper-src/RaspberryPi_JetsonNano/python/lib/waveshare_epd \
      /home/magnus/repos/skald/src/skald/vendor/

echo "==> sanity-check import"
/home/magnus/repos/skald/.venv/bin/python -c "
import sys
sys.path.insert(0, '/home/magnus/repos/skald/src/skald/vendor')
from waveshare_epd import epd2in13_V4
print('EPD class OK:', epd2in13_V4.EPD)
"

echo "==> (re)start skald-mcp.service"
sudo systemctl restart skald-mcp.service
sleep 3
systemctl status skald-mcp.service --no-pager -l | head -25
REMOTE
)

echo "$REMOTE_SCRIPT" | ssh skald 'cat > /tmp/skald-pi-cleanup.sh && chmod +x /tmp/skald-pi-cleanup.sh'
ssh -t skald 'bash /tmp/skald-pi-cleanup.sh'
