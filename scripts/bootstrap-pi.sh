#!/usr/bin/env bash
# Run ON skald (the Pi), not on the laptop.
# Idempotent — safe to re-run.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/magnus/repos/skald}"

echo "==> apt deps"
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    python3-dev libjpeg-dev zlib1g-dev libtiff6 libopenjp2-7 \
    git rsync curl

echo "==> SPI enable (best-effort — needs reboot to take effect)"
if command -v raspi-config >/dev/null; then
    sudo raspi-config nonint do_spi 0 || true
fi

echo "==> groups (spi, gpio, i2c)"
sudo usermod -aG spi,gpio,i2c "$USER" || true

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

echo "==> stop any stop-gap dry-run MCP (port 8765)"
pkill -f "skald serve" || true
sleep 1

echo "==> user systemd unit (no sudo needed for restarts)"
loginctl enable-linger "$USER"
mkdir -p ~/.config/systemd/user
install -m 0644 "$REPO_DIR/deploy/skald-mcp.service" ~/.config/systemd/user/skald-mcp.service
systemctl --user daemon-reload

echo "==> enable + start"
systemctl --user enable --now skald-mcp.service

echo ""
echo "Bootstrap complete."
echo "  systemctl --user status skald-mcp.service"
echo "  journalctl --user -u skald-mcp.service -f"
echo ""
echo "If SPI was just enabled, the panel won't draw until you reboot:"
echo "  sudo reboot"
