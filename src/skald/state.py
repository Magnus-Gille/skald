"""Persistent state + refresh budget for Skald."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

STATE_PATH_ENV = "SKALD_STATE_PATH"
_DEFAULT_STATE_PATH = Path("/var/lib/skald/state.json")
_LOCAL_FALLBACK = Path.home() / ".local/share/skald/state.json"

# token bucket
MCP_REFRESHES_PER_HOUR = 6
PARTIAL_BEFORE_FORCED_FULL = 12
HOURS_BEFORE_FORCED_FULL = 6


def state_path() -> Path:
    p = os.environ.get(STATE_PATH_ENV)
    if p:
        return Path(p)
    if _DEFAULT_STATE_PATH.parent.exists() and os.access(_DEFAULT_STATE_PATH.parent, os.W_OK):
        return _DEFAULT_STATE_PATH
    _LOCAL_FALLBACK.parent.mkdir(parents=True, exist_ok=True)
    return _LOCAL_FALLBACK


@dataclass
class State:
    verse: list[str] = field(default_factory=lambda: ["", "", ""])
    verse_source: str = "boot"  # "mcp" once an agent has written
    footer: str = "the watch begins"
    footer_source: str = "boot"  # "mcp"
    last_full_refresh: float = 0.0
    last_partial_refresh: float = 0.0
    partials_since_full: int = 0
    recent_verses: list[list[str]] = field(default_factory=list)  # last ~24 verses
    bucket_window_start: float = 0.0
    bucket_used: int = 0

    @classmethod
    def load(cls) -> "State":
        p = state_path()
        if not p.exists():
            return cls()
        try:
            data = json.loads(p.read_text())
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError):
            return cls()

    def save(self) -> None:
        p = state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2, sort_keys=True))
        tmp.replace(p)

    def needs_full_refresh(self) -> bool:
        if self.last_full_refresh == 0.0:
            return True
        if self.partials_since_full >= PARTIAL_BEFORE_FORCED_FULL:
            return True
        if time.time() - self.last_full_refresh > HOURS_BEFORE_FORCED_FULL * 3600:
            return True
        return False

    def effective_bucket_used(self) -> int:
        """How many tokens are consumed in the *current* window.

        Returns 0 if the window has already elapsed — the reset is lazy and
        only persisted on the next `take_token`, but callers reading the
        budget should see the post-reset value.
        """
        if time.time() - self.bucket_window_start > 3600:
            return 0
        return self.bucket_used

    def take_token(self) -> Optional[str]:
        """Returns None if a refresh is allowed, otherwise an error message."""
        now = time.time()
        if now - self.bucket_window_start > 3600:
            self.bucket_window_start = now
            self.bucket_used = 0
        if self.bucket_used >= MCP_REFRESHES_PER_HOUR:
            wait_s = int(3600 - (now - self.bucket_window_start))
            return f"refresh budget exhausted; try again in {wait_s}s"
        self.bucket_used += 1
        return None

    def record_refresh(self, partial: bool) -> None:
        now = time.time()
        if partial:
            self.last_partial_refresh = now
            self.partials_since_full += 1
        else:
            self.last_full_refresh = now
            self.last_partial_refresh = now
            self.partials_since_full = 0

    def remember_verse(self, lines: list[str]) -> None:
        if not any(lines):
            return
        self.recent_verses = ([list(lines)] + self.recent_verses)[:24]
