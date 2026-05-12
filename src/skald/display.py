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
    """Composes black + red planes into a visible RGB PNG."""

    RED_RGB = (190, 40, 40)

    def __init__(self, out_path: Optional[Path] = None):
        self.out_path = Path(out_path or os.environ.get("SKALD_PREVIEW_PATH", "/tmp/skald-preview.png"))

    def show(self, black: Image.Image, red: Image.Image, partial: bool = False) -> None:
        for name, im in (("black", black), ("red", red)):
            if im.size != (CANVAS_W, CANVAS_H):
                raise ValueError(f"{name} image must be {CANVAS_W}x{CANVAS_H}, got {im.size}")
        b = black.convert("1", dither=Image.Dither.NONE)
        r = red.convert("1", dither=Image.Dither.NONE)
        out = Image.new("RGB", (CANVAS_W, CANVAS_H), (255, 255, 255))
        bp, rp = b.load(), r.load()
        op = out.load()
        for y in range(CANVAS_H):
            for x in range(CANVAS_W):
                if bp[x, y] == 0:
                    op[x, y] = (0, 0, 0)
                elif rp[x, y] == 0:
                    op[x, y] = self.RED_RGB
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        out.save(self.out_path)

    def clear(self) -> None:
        blank = Image.new("1", (CANVAS_W, CANVAS_H), 1)
        self.show(blank, blank)


class WaveshareDisplay:
    """Wraps Waveshare's epd2in13b_V4 (B/W/R tri-color) driver.

    We render monochrome; the red plane is always blank-white. The B-variant
    has no usable partial refresh (red ink needs the full ~15s cycle), so
    every show() is a full refresh — `partial` is accepted for API parity
    but ignored.
    """

    def __init__(self):
        vendor = Path(__file__).parent / "vendor"
        if vendor.exists() and str(vendor) not in sys.path:
            sys.path.insert(0, str(vendor))
        from waveshare_epd import epd2in13b_V4  # type: ignore
        self._mod = epd2in13b_V4
        self._epd = epd2in13b_V4.EPD()
        self._blank_red = Image.new("1", (CANVAS_W, CANVAS_H), 1)  # all white = no red

    def _to_buffer(self, img: Image.Image) -> bytes:
        if img.size != (CANVAS_W, CANVAS_H):
            raise ValueError(f"image must be {CANVAS_W}x{CANVAS_H}, got {img.size}")
        if img.mode != "1":
            img = img.convert("1", dither=Image.Dither.NONE)
        # B-variant ribbon mounts opposite to the plain V4 — rotate so up is up.
        return self._epd.getbuffer(img.rotate(180))

    def show(self, black: Image.Image, red: Image.Image, partial: bool = False) -> None:
        self._epd.init()
        self._epd.display(self._to_buffer(black), self._to_buffer(red))
        self._epd.sleep()

    def clear(self) -> None:
        self._epd.init()
        if hasattr(self._epd, "Clear"):
            self._epd.Clear()
        else:
            blank = self._to_buffer(self._blank_red)
            self._epd.display(blank, blank)
        self._epd.sleep()


def get_display(dry_run: bool = False, out_path: Optional[Path] = None):
    if dry_run or not is_pi():
        return DryRunDisplay(out_path=out_path)
    return WaveshareDisplay()
