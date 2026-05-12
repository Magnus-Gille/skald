"""Pillow drawing for Skald's Watch — 250×122 1-bit."""

from __future__ import annotations

from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from . import CANVAS_H, CANVAS_W

BLACK = 0
WHITE = 1  # mode "1": 0=black, 1=white

ROMAN = [
    "",
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
    "XXI", "XXII", "XXIII", "XXIV",
]

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _font_dir() -> Path:
    return Path(__file__).parent / "fonts"


def _load_font(name: str, size: int) -> ImageFont.ImageFont:
    """Load a vendored TTF if present, else fall back to PIL default."""
    p = _font_dir() / name
    if p.exists():
        try:
            return ImageFont.truetype(str(p), size=size)
        except OSError:
            pass
    # Fallback: PIL default (bitmap, but readable at small sizes)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _font_header() -> ImageFont.ImageFont:
    return _load_font("Inter-Medium.ttf", 11)


def _font_verse() -> ImageFont.ImageFont:
    return _load_font("EBGaramond-Italic.ttf", 16)


def _font_footer() -> ImageFont.ImageFont:
    return _load_font("Inter-Regular.ttf", 10)


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    l, _, r, _ = draw.textbbox((0, 0), text, font=font)
    return r - l


def _draw_centered(draw, y: int, text: str, font) -> None:
    w = _text_w(draw, text, font)
    draw.text(((CANVAS_W - w) // 2, y), text, font=font, fill=BLACK)


def header_text(now: datetime) -> tuple[str, str]:
    day = DAY_ABBR[now.weekday()]
    mon = MONTH_ABBR[now.month - 1]
    left = f"{day} · {now.day} {mon} {now.year}"
    hour_24 = now.hour if now.hour > 0 else 24
    right = f"hour {ROMAN[hour_24]}"
    return left, right


def render(
    verse: list[str],
    footer: str,
    now: Optional[datetime] = None,
) -> Image.Image:
    """Render the full watch face to a 250×122 1-bit image."""
    now = now or datetime.now()
    img = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(img)

    f_h = _font_header()
    f_v = _font_verse()
    f_f = _font_footer()

    # --- Header (y ~ 0..16)
    left, right = header_text(now)
    draw.text((6, 1), left, font=f_h, fill=BLACK)
    rw = _text_w(draw, right, f_h)
    draw.text((CANVAS_W - rw - 6, 1), right, font=f_h, fill=BLACK)

    # --- Top divider (dotted)
    for x in range(6, CANVAS_W - 6, 3):
        draw.point((x, 18), fill=BLACK)

    # --- Verse (y ~ 22..92): three lines, centered, generously spaced
    lines = list(verse) + ["", "", ""]
    lines = lines[:3]
    line_h = 18
    block_h = line_h * 3
    top = 22 + ((CANVAS_H - 22 - 28) - block_h) // 2  # center between dividers
    for i, line in enumerate(lines):
        if line:
            _draw_centered(draw, top + i * line_h, line, f_v)

    # --- Bottom divider
    for x in range(6, CANVAS_W - 6, 3):
        draw.point((x, CANVAS_H - 16), fill=BLACK)

    # --- Footer (y ~ CANVAS_H - 13)
    draw.text((6, CANVAS_H - 13), footer, font=f_f, fill=BLACK)

    return img


def render_clear() -> Image.Image:
    return Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
