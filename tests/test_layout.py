"""Layout smoke tests + golden-image guard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image

from skald import CANVAS_H, CANVAS_W, layout

GOLDEN = Path(__file__).parent / "golden"
GOLDEN.mkdir(exist_ok=True)


def _fixed_now() -> datetime:
    return datetime(2026, 5, 12, 13, 0)


def test_canvas_size_and_mode():
    img = layout.render(
        verse=["the small lamp is patient,", "the page does not hurry —", "outside, a bird begins."],
        footer="14° clear · the watch is clear",
        now=_fixed_now(),
    )
    assert img.size == (CANVAS_W, CANVAS_H)
    assert img.mode == "1"


def test_empty_verse_renders():
    img = layout.render(verse=["", "", ""], footer="", now=_fixed_now())
    # Should still be 1-bit at the right size and not crash on empty strings.
    assert img.size == (CANVAS_W, CANVAS_H)
    assert img.mode == "1"


def test_header_text():
    left, right = layout.header_text(_fixed_now())
    assert left == "Tue · 12 May 2026"
    assert right == "hour XIII"


def test_clear_is_white():
    img = layout.render_clear()
    assert img.size == (CANVAS_W, CANVAS_H)
    assert img.mode == "1"
    # All pixels should be white (1).
    assert img.getextrema() == (1, 1)


def test_golden_match():
    """Render with fixed inputs and compare to checked-in golden if present.

    On first run with no golden, write it and pass — the file becomes the
    reference for future runs.
    """
    img = layout.render(
        verse=["the small lamp is patient,", "the page does not hurry —", "outside, a bird begins."],
        footer="14° clear · the watch is clear",
        now=_fixed_now(),
    )
    gp = GOLDEN / "watch_default.png"
    if not gp.exists():
        img.save(gp)
        return
    ref = Image.open(gp).convert("1")
    assert img.tobytes() == ref.tobytes(), "layout drifted from golden; re-render and review"
