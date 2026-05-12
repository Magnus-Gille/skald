#!/usr/bin/env bash
# Run ON skald (the Pi), not on the laptop.
# Idempotent — safe to re-run.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/magnus/repos/skald}"
ENV_DIR="/etc/skald"
STATE_DIR="/var/lib/skald"

echo "==> apt deps"
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    python3-dev libjpeg-dev zlib1g-dev libtiff6 libopenjp2-7 \
    git rsync curl

echo "==> SPI enable (best-effort)"
if command -v raspi-config >/dev/null; then
    sudo raspi-config nonint do_spi 0 || true
fi

echo "==> groups (spi, gpio, i2c)"
sudo usermod -aG spi,gpio,i2c "$USER" || true

echo "==> dirs"
sudo install -d -m 0750 -o root -g "$USER" "$ENV_DIR"
sudo install -d -m 0750 -o "$USER" -g "$USER" "$STATE_DIR"
if [ ! -f "$ENV_DIR/skald.env" ]; then
    if [ -f "$REPO_DIR/deploy/skald.env.example" ]; then
        sudo install -m 0640 -o root -g "$USER" "$REPO_DIR/deploy/skald.env.example" "$ENV_DIR/skald.env"
        echo "    placed example env at $ENV_DIR/skald.env — edit it with the real ANTHROPIC_API_KEY"
    fi
fi

echo "==> vendor the Waveshare driver"
VENDOR_DIR="$REPO_DIR/src/skald/vendor"
mkdir -p "$VENDOR_DIR"
if [ ! -d "$VENDOR_DIR/waveshare_epd" ]; then
    tmp=$(mktemp -d)
    git clone --depth 1 https://github.com/waveshareteam/e-Paper "$tmp/e-Paper"
    cp -r "$tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd" "$VENDOR_DIR/"
    rm -rf "$tmp"
    echo "    vendored to $VENDOR_DIR/waveshare_epd"
fi

echo "==> venv + install"
if [ ! -d "$REPO_DIR/.venv" ]; then
    python3 -m venv "$REPO_DIR/.venv"
fi
"$REPO_DIR/.venv/bin/pip" install --upgrade pip
"$REPO_DIR/.venv/bin/pip" install -e "$REPO_DIR[pi]"

echo "==> systemd units"
sudo install -m 0644 "$REPO_DIR/deploy/skald-mcp.service"  /etc/systemd/system/skald-mcp.service
sudo install -m 0644 "$REPO_DIR/deploy/skald-tick.service" /etc/systemd/system/skald-tick.service
sudo install -m 0644 "$REPO_DIR/deploy/skald-tick.timer"   /etc/systemd/system/skald-tick.timer
sudo systemctl daemon-reload

echo "==> enable + start"
sudo systemctl enable --now skald-mcp.service
sudo systemctl enable --now skald-tick.timer

echo ""
echo "Bootstrap complete."
echo "  systemctl status skald-mcp.service skald-tick.timer"
echo "  journalctl -u skald-mcp.service -f"
echo "  curl http://localhost:8765/mcp -X POST -H 'content-type: application/json' --data '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'"
