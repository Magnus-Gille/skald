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
    return _load_font("Bitter-Bold.ttf", 16)


def _font_footer() -> ImageFont.ImageFont:
    return _load_font("Inter-Regular.ttf", 10)


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    l, _, r, _ = draw.textbbox((0, 0), text, font=font)
    return r - l


def _draw_centered(draw, y: int, text: str, font) -> None:
    w = _text_w(draw, text, font)
    draw.text(((CANVAS_W - w) // 2, y), text, font=font, fill=BLACK)


VERSE_MAX_WIDTH = CANVAS_W - 12  # 6px margin each side


def measure_verse_overflow(lines: list[str]) -> list[dict]:
    """Return per-line overflow info; empty list if everything fits."""
    if not any(lines):
        return []
    probe = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(probe)
    f = _font_verse()
    bad = []
    for i, line in enumerate(lines):
        if not line:
            continue
        w = _text_w(draw, line, f)
        if w > VERSE_MAX_WIDTH:
            bad.append({"line": i + 1, "chars": len(line), "px": w, "max_px": VERSE_MAX_WIDTH})
    return bad


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
) -> tuple[Image.Image, Image.Image]:
    """Render the full watch face.

    Returns (black_img, red_img), both 250×122 mode "1". On the tri-color
    panel: pixels=0 in black_img → black ink; pixels=0 in red_img → red ink;
    pixels=1 in both → bare e-paper white. Red is reserved for rubrication
    — the roman-numeral hour and the two dotted dividers.
    """
    now = now or datetime.now()
    black = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    red = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    f_h = _font_header()
    f_v = _font_verse()
    f_f = _font_footer()

    # --- Header (y ~ 0..16): date black, roman-numeral hour red
    left, right = header_text(now)
    db.text((6, 1), left, font=f_h, fill=BLACK)
    rw = _text_w(db, right, f_h)
    dr.text((CANVAS_W - rw - 6, 1), right, font=f_h, fill=BLACK)

    # --- Top divider (dotted, red rubrication)
    for x in range(6, CANVAS_W - 6, 3):
        dr.point((x, 18), fill=BLACK)

    # --- Verse: three lines, centered, generously spaced (black)
    lines = list(verse) + ["", "", ""]
    lines = lines[:3]
    line_h = 20
    block_h = line_h * 3
    top = 22 + ((CANVAS_H - 22 - 28) - block_h) // 2
    for i, line in enumerate(lines):
        if line:
            _draw_centered(db, top + i * line_h, line, f_v)

    # --- Bottom divider (dotted, red)
    for x in range(6, CANVAS_W - 6, 3):
        dr.point((x, CANVAS_H - 16), fill=BLACK)

    # --- Footer (black)
    db.text((6, CANVAS_H - 13), footer, font=f_f, fill=BLACK)

    return black, red


def render_clear() -> tuple[Image.Image, Image.Image]:
    blank = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    return blank, blank.copy()
