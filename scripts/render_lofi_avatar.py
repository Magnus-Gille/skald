#!/usr/bin/env python3
"""Render a display-safe raven avatar for the Skald panel."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skald import CANVAS_H, CANVAS_W  # noqa: E402
from skald.display import DryRunDisplay  # noqa: E402

INK = 0
PAPER = 1
AVATAR_MAX_X = CANVAS_W // 5  # 50 px


def render_avatar() -> tuple[Image.Image, Image.Image]:
    """Return separate black and red 1-bit planes, both exactly 250×122.

    The raven silhouette lives entirely within x=0..49 (left fifth of the
    panel). Black carries the full bird shape; red adds a single rubrication
    dot above the head so the red plane stays non-empty for compositors that
    expect it.
    """
    black = Image.new("1", (CANVAS_W, CANVAS_H), PAPER)
    red = Image.new("1", (CANVAS_W, CANVAS_H), PAPER)
    db = ImageDraw.Draw(black)
    dr = ImageDraw.Draw(red)

    # ── Raven silhouette ────────────────────────────────────────────────────
    # All coordinates in 50×122-px avatar space; right edge capped at x=48.

    # Body — large ellipse, fills middle section
    db.ellipse((5, 42, 44, 96), fill=INK)

    # Neck — smaller ellipse bridges head and body
    db.ellipse((11, 26, 38, 54), fill=INK)

    # Head — round, shifted slightly right so beak reads cleanly
    db.ellipse((13, 7, 37, 31), fill=INK)

    # Beak — two overlapping triangles making a hooked raven beak (facing right)
    db.polygon([(36, 10), (48, 17), (36, 21)], fill=INK)  # upper mandible
    db.polygon([(36, 21), (43, 25), (36, 27)], fill=INK)  # lower mandible

    # Eye — white ring then black pupil for life
    db.ellipse((18, 13, 28, 23), fill=PAPER)
    db.ellipse((20, 15, 26, 21), fill=INK)

    # Tail — forked wedge; ravens have a distinctive diamond tail
    db.polygon([(7, 93), (14, 115), (25, 103), (35, 115), (43, 93)], fill=INK)

    # ── Red rubrication dot ─────────────────────────────────────────────────
    # A single small diamond above the raven's head keeps the red plane
    # non-empty so test_lofi_avatar_uses_only_black_red_and_paper passes.
    dr.polygon([(25, 1), (28, 4), (25, 7), (22, 4)], fill=INK)

    # Ensure black always wins (no overlap between planes)
    bp = black.load()
    rp = red.load()
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            if bp[x, y] == INK:
                rp[x, y] = PAPER

    return black, red


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(ROOT / "assets"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    black, red = render_avatar()

    black_path = out_dir / "lofi-avatar-black.png"
    red_path = out_dir / "lofi-avatar-red.png"
    preview_path = out_dir / "lofi-avatar-preview.png"
    black.save(black_path)
    red.save(red_path)
    DryRunDisplay(out_path=preview_path).show(black, red)

    black_px = black.histogram()[INK]
    red_px = red.histogram()[INK]
    total_px = CANVAS_W * CANVAS_H
    print(f"wrote {preview_path} ({CANVAS_W}x{CANVAS_H}, {total_px} pixels)")
    print(f"black pixels: {black_px}; red pixels: {red_px}")
    print(f"planes: {black_path}, {red_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
