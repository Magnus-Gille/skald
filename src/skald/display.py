"""Display driver — Waveshare 2.13" V4 with a dry-run PNG renderer."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PIL import Image

from . import CANVAS_H, CANVAS_W


def is_pi() -> bool:
    """True when running on a Pi-like host with the Waveshare driver available."""
    if os.environ.get("SKALD_FORCE_DRYRUN") == "1":
        return False
    try:
        import RPi.GPIO  # noqa: F401
        return True
    except Exception:
        return False


class DryRunDisplay:
    """Writes the framebuffer to a PNG, byte-equivalent to what the panel would receive."""

    def __init__(self, out_path: Optional[Path] = None):
        self.out_path = Path(out_path or os.environ.get("SKALD_PREVIEW_PATH", "/tmp/skald-preview.png"))

    def show(self, img: Image.Image, partial: bool = False) -> None:
        if img.size != (CANVAS_W, CANVAS_H):
            raise ValueError(f"image must be {CANVAS_W}x{CANVAS_H}, got {img.size}")
        if img.mode != "1":
            img = img.convert("1", dither=Image.Dither.NONE)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(self.out_path)

    def clear(self) -> None:
        self.show(Image.new("1", (CANVAS_W, CANVAS_H), 1))


class WaveshareDisplay:
    """Wraps Waveshare's epd2in13_V4 driver. Lazy-imports so non-Pi machines stay clean."""

    def __init__(self):
        # Vendored driver lives at src/skald/vendor/waveshare/
        vendor = Path(__file__).parent / "vendor"
        if vendor.exists() and str(vendor) not in sys.path:
            sys.path.insert(0, str(vendor))
        from waveshare_epd import epd2in13_V4  # type: ignore
        self._mod = epd2in13_V4
        self._epd = epd2in13_V4.EPD()

    def _to_buffer(self, img: Image.Image) -> bytes:
        if img.size != (CANVAS_W, CANVAS_H):
            raise ValueError(f"image must be {CANVAS_W}x{CANVAS_H}, got {img.size}")
        if img.mode != "1":
            img = img.convert("1", dither=Image.Dither.NONE)
        return self._epd.getbuffer(img)

    def show(self, img: Image.Image, partial: bool = False) -> None:
        buf = self._to_buffer(img)
        if partial:
            self._epd.init_fast() if hasattr(self._epd, "init_fast") else self._epd.init()
            self._epd.displayPartial(buf) if hasattr(self._epd, "displayPartial") else self._epd.display(buf)
        else:
            self._epd.init()
            self._epd.Clear(0xFF) if hasattr(self._epd, "Clear") else None
            self._epd.display(buf)
        self._epd.sleep()

    def clear(self) -> None:
        self._epd.init()
        if hasattr(self._epd, "Clear"):
            self._epd.Clear(0xFF)
        else:
            self._epd.display(self._epd.getbuffer(Image.new("1", (CANVAS_W, CANVAS_H), 1)))
        self._epd.sleep()


def get_display(dry_run: bool = False, out_path: Optional[Path] = None):
    if dry_run or not is_pi():
        return DryRunDisplay(out_path=out_path)
    return WaveshareDisplay()
