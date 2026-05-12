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
    black, red = layout.render(
        verse=["the small lamp is patient,", "the page does not hurry —", "outside, a bird begins."],
        footer="14° clear · the watch is clear",
        now=_fixed_now(),
    )
    for im in (black, red):
        assert im.size == (CANVAS_W, CANVAS_H)
        assert im.mode == "1"


def test_empty_verse_renders():
    black, red = layout.render(verse=["", "", ""], footer="", now=_fixed_now())
    for im in (black, red):
        assert im.size == (CANVAS_W, CANVAS_H)
        assert im.mode == "1"


def test_header_text():
    left, right = layout.header_text(_fixed_now())
    assert left == "Tue · 12 May 2026"
    assert right == "hour XIII"


def test_clear_is_white():
    black, red = layout.render_clear()
    for im in (black, red):
        assert im.size == (CANVAS_W, CANVAS_H)
        assert im.mode == "1"
        assert im.getextrema() == (1, 1)


def test_red_plane_has_rubrication():
    """Red plane should contain ink (dividers + hour); not be empty."""
    _, red = layout.render(
        verse=["a", "b", "c"], footer="", now=_fixed_now(),
    )
    # At least one black pixel (=red ink) somewhere in the red plane.
    assert red.getextrema() == (0, 1), "red plane should have at least one inked pixel"


def test_golden_match():
    """Render with fixed inputs and compare to checked-in golden if present."""
    black, red = layout.render(
        verse=["the small lamp is patient,", "the page does not hurry —", "outside, a bird begins."],
        footer="14° clear · the watch is clear",
        now=_fixed_now(),
    )
    for plane, name in ((black, "watch_default_black.png"), (red, "watch_default_red.png")):
        gp = GOLDEN / name
        if not gp.exists():
            plane.save(gp)
            continue
        ref = Image.open(gp).convert("1")
        assert plane.tobytes() == ref.tobytes(), f"{name}: layout drifted; re-render and review"
