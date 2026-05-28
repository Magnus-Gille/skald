"""Pillow drawing for Skald's Watch — 250×122 1-bit."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from . import CANVAS_H, CANVAS_W

BLACK = 0
WHITE = 1  # mode "1": 0=black, 1=white

# Avatar column geometry (left fifth of panel)
AVATAR_W = 50           # pixel column width
AVATAR_SEP_X = AVATAR_W # vertical separator drawn here
CONTENT_X = AVATAR_W + 2 # content column starts here (2px gap after sep)
CONTENT_RIGHT_MARGIN = 6

# Named font styles
FONT_STYLES: dict[str, dict] = {
    "serif": {
        "verse": ("Bitter-Bold.ttf", 16),
        "header": ("Inter-Medium.ttf", 11),
        "footer": ("Inter-Regular.ttf", 10),
        "line_h": 20,
    },
    "pixel": {
        "verse": ("haxrcorp4089.ttf", 20),
        "header": ("helvb08.ttf", 10),
        "footer": ("Born2bSportyV2.ttf", 10),
        "line_h": 22,
    },
    "sporty": {
        "verse": ("Born2bSportyV2.ttf", 15),
        "header": ("Born2bSportyV2.ttf", 10),
        "footer": ("helvb08.ttf", 10),
        "line_h": 20,
    },
    "gravity": {
        "verse": ("GravityBold8.ttf", 16),
        "header": ("helvb08.ttf", 10),
        "footer": ("helvb08.ttf", 10),
        "line_h": 20,
    },
}
DEFAULT_STYLE = "serif"

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
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fonts(style: str = DEFAULT_STYLE) -> tuple:
    """Return (f_verse, f_header, f_footer) for the given style name."""
    s = FONT_STYLES.get(style, FONT_STYLES[DEFAULT_STYLE])
    return (
        _load_font(*s["verse"]),
        _load_font(*s["header"]),
        _load_font(*s["footer"]),
    )


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    l, _, r, _ = draw.textbbox((0, 0), text, font=font)
    return r - l


def _draw_centered(draw, y: int, text: str, font, x_start: int, x_end: int) -> None:
    w = _text_w(draw, text, font)
    x = x_start + max(0, (x_end - x_start - w) // 2)
    draw.text((x, y), text, font=font, fill=BLACK)


def _verse_max_width(has_avatar: bool) -> int:
    if has_avatar:
        return CANVAS_W - CONTENT_X - CONTENT_RIGHT_MARGIN
    return CANVAS_W - 12


def measure_verse_overflow(
    lines: list[str],
    style: str = DEFAULT_STYLE,
    has_avatar: bool = False,
) -> list[dict]:
    """Return per-line overflow info; empty list if everything fits."""
    if not any(lines):
        return []
    probe = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(probe)
    f_verse, _, _ = _fonts(style)
    max_w = _verse_max_width(has_avatar)
    bad = []
    for i, line in enumerate(lines):
        if not line:
            continue
        w = _text_w(draw, line, f_verse)
        if w > max_w:
            bad.append({"line": i + 1, "chars": len(line), "px": w, "max_px": max_w})
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
    style: str = DEFAULT_STYLE,
    avatar: Optional[Image.Image] = None,
) -> tuple[Image.Image, Image.Image]:
    """Render the full watch face.

    Returns (black_img, red_img), both 250×122 mode "1". On the tri-color
    panel: pixels=0 in black_img → black ink; pixels=0 in red_img → red ink;
    pixels=1 in both → bare e-paper white. Red is reserved for rubrication
    — the roman-numeral hour, the two dotted horizontal dividers, and (when
    an avatar is present) the dotted vertical separator.

    avatar: a PIL image of any size/mode. It will be converted to 1-bit and
    scaled to fill the left AVATAR_W × CANVAS_H column.
    """
    now = now or datetime.now()
    black = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    red = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    f_v, f_h, f_f = _fonts(style)
    line_h = FONT_STYLES.get(style, FONT_STYLES[DEFAULT_STYLE]).get("line_h", 20)

    if avatar is not None:
        # Scale avatar to exactly fill the left column, paste into black plane
        av = avatar.convert("1").resize((AVATAR_W, CANVAS_H), Image.LANCZOS)
        black.paste(av, (0, 0))
        # Dotted vertical separator in red
        for y in range(0, CANVAS_H, 3):
            dr.point((AVATAR_SEP_X, y), fill=BLACK)
        cx = CONTENT_X
    else:
        cx = 6

    x_end = CANVAS_W - CONTENT_RIGHT_MARGIN  # right edge of content

    # --- Header: date left, roman-numeral hour right (red)
    left, right = header_text(now)
    db.text((cx, 1), left, font=f_h, fill=BLACK)
    rw = _text_w(db, right, f_h)
    dr.text((CANVAS_W - rw - CONTENT_RIGHT_MARGIN, 1), right, font=f_h, fill=BLACK)

    # --- Top divider (dotted, red)
    for x in range(cx, x_end, 3):
        dr.point((x, 18), fill=BLACK)

    # --- Verse: three lines, centered within content column
    lines = list(verse) + ["", "", ""]
    lines = lines[:3]
    block_h = line_h * 3
    verse_zone_h = CANVAS_H - 22 - 28  # same zone as before
    top = 22 + (verse_zone_h - block_h) // 2
    for i, line in enumerate(lines):
        if line:
            _draw_centered(db, top + i * line_h, line, f_v, cx, x_end)

    # --- Bottom divider (dotted, red)
    for x in range(cx, x_end, 3):
        dr.point((x, CANVAS_H - 16), fill=BLACK)

    # --- Footer
    db.text((cx, CANVAS_H - 13), footer, font=f_f, fill=BLACK)

    return black, red


def render_clear() -> tuple[Image.Image, Image.Image]:
    blank = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    return blank, blank.copy()


# --- Airport split-flap board -------------------------------------------------

BOARD_FONT = "GravityBold8.ttf"
BOARD_MARGIN = 3
BOARD_GAP = 2
BOARD_MAX_COLS = 16


def _fit_board_font(tile_w: int, tile_h: int):
    """Largest BOARD_FONT that fits comfortably inside a tile.

    Tiles are usually taller than wide, so width is the binding constraint —
    size to the narrow dimension or letters spill past the tile edges.
    """
    size = max(6, int(min(tile_w, tile_h) * 0.92))
    return _load_font(BOARD_FONT, size)


def render_board(
    rows: list[str],
    seam: bool = True,
) -> tuple[Image.Image, Image.Image]:
    """Render text as a grid of split-flap tiles — an airport departures board.

    Each character sits in its own black tile with the letter in reverse video
    (white on black). A thin red seam cuts across the middle of every tile,
    the way a real split-flap card hinges. No header, no footer — just the
    block. Rows are uppercased and padded to a common width so the whole thing
    reads as one solid rectangle of flaps.

    Returns (black_img, red_img), both 250×122 mode "1", same convention as
    `render`: 0 = ink, 1 = bare panel; red plane carries the seam.
    """
    black = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    red = Image.new("1", (CANVAS_W, CANVAS_H), WHITE)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    rows = [r.upper() for r in rows if r is not None] or [""]
    ncols = min(BOARD_MAX_COLS, max(1, max(len(r) for r in rows)))
    nrows = len(rows)

    avail_w = CANVAS_W - 2 * BOARD_MARGIN - (ncols - 1) * BOARD_GAP
    avail_h = CANVAS_H - 2 * BOARD_MARGIN - (nrows - 1) * BOARD_GAP
    tile_w = avail_w // ncols
    tile_h = avail_h // nrows

    grid_w = ncols * tile_w + (ncols - 1) * BOARD_GAP
    grid_h = nrows * tile_h + (nrows - 1) * BOARD_GAP
    ox = (CANVAS_W - grid_w) // 2
    oy = (CANVAS_H - grid_h) // 2

    font = _fit_board_font(tile_w, tile_h)

    for r, row in enumerate(rows):
        padded = row[:ncols].ljust(ncols)
        for c in range(ncols):
            ch = padded[c]
            x0 = ox + c * (tile_w + BOARD_GAP)
            y0 = oy + r * (tile_h + BOARD_GAP)
            x1 = x0 + tile_w - 1
            y1 = y0 + tile_h - 1
            db.rectangle([x0, y0, x1, y1], fill=BLACK)
            if ch != " ":
                db.text(
                    (x0 + tile_w / 2, y0 + tile_h / 2),
                    ch, font=font, fill=WHITE, anchor="mm",
                )
            if seam:
                ymid = y0 + tile_h // 2
                db.line([x0, ymid, x1, ymid], fill=WHITE)   # carve a bare seam
                dr.line([x0, ymid, x1, ymid], fill=BLACK)   # paint it red

    return black, red
