"""One-off dashboard mockup pushed to the panel.

Run on the Pi via skald's venv. The skald-mcp service holds /dev/spidev*
only during a render (sleep() releases it), so stopping it first avoids
any race on the SPI bus.
"""
from __future__ import annotations

import math
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Make `skald` importable when running outside an install
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skald import CANVAS_H, CANVAS_W  # noqa: E402
from skald.display import get_display  # noqa: E402

FONT_DIR = Path(__file__).resolve().parents[1] / "src" / "skald" / "fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size=size)


def render():
    black = Image.new("1", (CANVAS_W, CANVAS_H), 1)
    red = Image.new("1", (CANVAS_W, CANVAS_H), 1)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    f_label = font("Inter-Regular.ttf", 9)
    f_big = font("Bitter-Bold.ttf", 28)
    f_mid = font("Bitter-Bold.ttf", 14)
    f_small = font("Inter-Medium.ttf", 10)

    # --- Header strip
    db.text((6, 1), "SKALD · DASHBOARD", font=f_small, fill=0)
    t = datetime.now().strftime("%H:%M")
    tw = db.textlength(t, font=f_small)
    db.text((CANVAS_W - tw - 6, 1), t, font=f_small, fill=0)

    # red divider
    for x in range(6, CANVAS_W - 6, 3):
        dr.point((x, 16), fill=0)

    # --- Left zone: big number "42°"
    db.text((6, 22), "42", font=f_big, fill=0)
    db.text((52, 26), "°C", font=f_mid, fill=0)
    db.text((6, 60), "outside", font=f_label, fill=0)
    # tiny up-arrow trend in red
    dr.polygon([(50, 64), (56, 64), (53, 58)], fill=0)
    db.text((58, 58), "+3", font=f_label, fill=0)

    # --- Middle zone: vertical bar chart (mixed black/red)
    bx0 = 88
    bw = 8
    gap = 4
    base_y = 78
    bars = [22, 38, 30, 56, 44, 60, 48, 36]
    for i, h in enumerate(bars):
        x0 = bx0 + i * (bw + gap)
        target = dr if i % 2 == 1 else db
        target.rectangle([x0, base_y - h, x0 + bw, base_y], fill=0)
    # baseline
    db.line([bx0 - 2, base_y + 1, bx0 + len(bars) * (bw + gap), base_y + 1], fill=0)
    db.text((bx0, 82), "load · 8h", font=f_label, fill=0)

    # --- Right zone: donut gauge "87%"
    cx, cy, r = 215, 50, 22
    # outer ring (red arc 0..360 * 0.87)
    dr.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * 0.87), fill=0, width=4)
    # inner ring (remaining black thin)
    db.arc([cx - r, cy - r, cx + r, cy + r], start=-90 + int(360 * 0.87), end=270, fill=0, width=1)
    # label
    tw = db.textlength("87%", font=f_mid)
    db.text((cx - tw // 2, cy - 9), "87%", font=f_mid, fill=0)
    db.text((cx - 18, cy + r + 2), "uptime", font=f_label, fill=0)

    # --- Bottom red divider
    for x in range(6, CANVAS_W - 6, 3):
        dr.point((x, CANVAS_H - 18), fill=0)

    # --- Footer: tiny stats + sparkline
    db.text((6, CANVAS_H - 14), "▲12  ▼5  ◆99", font=f_label, fill=0)
    # sparkline on the right
    spark = [3, 5, 4, 7, 6, 8, 7, 9, 8, 10, 9, 11, 10, 9, 11, 12]
    sx0, sw, sh = 130, 110, 10
    base = CANVAS_H - 6
    lo, hi = min(spark), max(spark)
    pts = [
        (sx0 + i * (sw / (len(spark) - 1)),
         base - (v - lo) * sh / (hi - lo))
        for i, v in enumerate(spark)
    ]
    dr.line(pts, fill=0, width=1)
    # dot at last point
    lx, ly = pts[-1]
    dr.ellipse([lx - 2, ly - 2, lx + 2, ly + 2], fill=0)

    return black, red


def main() -> int:
    black, red = render()
    disp = get_display()
    print(f"display: {type(disp).__name__}")
    disp.show(black, red)
    print("pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
