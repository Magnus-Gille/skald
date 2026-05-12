"""Skald CLI entrypoint — `python -m skald {preview,serve,status}`."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def cmd_preview(args: argparse.Namespace) -> int:
    """Render a sample face to a PNG (for layout iteration without hardware)."""
    from . import layout
    verse = args.verse or [
        "the small lamp is patient,",
        "the page does not hurry —",
        "outside, a bird begins.",
    ]
    footer = args.footer if args.footer is not None else "the watch begins"
    from .display import DryRunDisplay
    black, red = layout.render(verse=verse, footer=footer, now=datetime.now())
    out = Path(args.out)
    DryRunDisplay(out_path=out).show(black, red)
    print(f"wrote {out} ({black.size[0]}x{black.size[1]} RGB w/ red)")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .mcp_server import build_server
    server = build_server(dry_run=args.dry_run, out_path=Path(args.out) if args.out else None)
    server.run(transport="http", host=args.host, port=args.port, path=args.path)
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    from dataclasses import asdict
    from .state import State
    print(json.dumps(asdict(State.load()), indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skald")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prev = sub.add_parser("preview", help="render a sample face to a PNG")
    p_prev.add_argument("--out", default="/tmp/skald-preview.png")
    p_prev.add_argument("--verse", nargs=3, metavar=("L1", "L2", "L3"), default=None)
    p_prev.add_argument("--footer", default=None)
    p_prev.set_defaults(func=cmd_preview)

    p_serve = sub.add_parser("serve", help="run the MCP HTTP server")
    p_serve.add_argument("--dry-run", action="store_true")
    p_serve.add_argument("--out", default=None)
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--path", default="/mcp")
    p_serve.set_defaults(func=cmd_serve)

    p_status = sub.add_parser("status", help="print current state JSON")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
