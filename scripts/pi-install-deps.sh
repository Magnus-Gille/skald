#!/usr/bin/env bash
# Run from laptop. Installs Pi-only deps (gpiozero, lgpio, RPi.GPIO, spidev)
# into the Pi venv, verifies the Waveshare driver loads end-to-end, and
# restarts skald-mcp.service.
set -euo pipefail

REMOTE_SCRIPT=$(cat <<'REMOTE'
#!/usr/bin/env bash
set -uo pipefail
cd /home/magnus/repos/skald

echo "==> apt: native build deps for lgpio (swig, headers)"
sudo apt-get install -y --no-install-recommends liblgpio-dev python3-lgpio swig build-essential python3-dev 2>&1 | tail -5

echo "==> install Pi extras into venv"
.venv/bin/pip install -e ".[pi]" 2>&1 | tail -15

echo "==> verify Waveshare driver loads (pin factory + all)"
.venv/bin/python -c "
import sys
sys.path.insert(0, 'src/skald/vendor')
from waveshare_epd import epd2in13_V4
print('EPD OK:', epd2in13_V4.EPD)
"

echo "==> restart skald-mcp.service"
sudo systemctl restart skald-mcp.service
sleep 3
systemctl status skald-mcp.service --no-pager -l | head -20
REMOTE
)

echo "$REMOTE_SCRIPT" | ssh skald 'cat > /tmp/skald-pi-install-deps.sh && chmod +x /tmp/skald-pi-install-deps.sh'
ssh -t skald 'bash /tmp/skald-pi-install-deps.sh'
