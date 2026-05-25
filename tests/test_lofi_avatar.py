"""Guards for the display-safe lofi avatar asset."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from skald import CANVAS_H, CANVAS_W

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_lofi_avatar.py"


def _load_avatar_module():
    spec = importlib.util.spec_from_file_location("render_lofi_avatar", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_lofi_avatar_planes_are_panel_native():
    mod = _load_avatar_module()
    black, red = mod.render_avatar()

    for plane in (black, red):
        assert plane.size == (CANVAS_W, CANVAS_H)
        assert plane.mode == "1"


def test_lofi_avatar_uses_only_black_red_and_paper():
    mod = _load_avatar_module()
    black, red = mod.render_avatar()

    bp = black.load()
    rp = red.load()
    black_px = 0
    red_px = 0
    overlap_px = 0
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            if bp[x, y] == mod.INK:
                black_px += 1
            if rp[x, y] == mod.INK:
                red_px += 1
            if bp[x, y] == mod.INK and rp[x, y] == mod.INK:
                overlap_px += 1

    assert black_px > 0
    assert red_px > 0
    assert overlap_px == 0


def test_lofi_avatar_fits_left_fifth_of_panel():
    mod = _load_avatar_module()
    black, red = mod.render_avatar()

    xs = []
    for plane in (black, red):
        px = plane.load()
        for y in range(CANVAS_H):
            for x in range(CANVAS_W):
                if px[x, y] == mod.INK:
                    xs.append(x)

    assert xs
    assert min(xs) >= 0
    assert max(xs) < CANVAS_W // 5
