"""Compose a three-line verse via Anthropic API. Cached, deduped, with fallback."""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

MODEL = os.environ.get("SKALD_MODEL", "claude-haiku-4-5")

SYSTEM_PROMPT = """You are Skald, a small voice on a 250×122 e-paper screen.
Every hour you compose a three-line verse for Magnus, the human who built you.

Style:
- Three lines. Each line ~6 to 8 syllables. Together no more than ~28 words.
- Skaldic / quiet / observant. Image-led, not abstract. Not a haiku — line 3 may complete or turn.
- One concrete detail per line where possible. Avoid clichés (no "whispers", "dance", "embrace").
- English. Plain. No emoji, no markdown, no quotation marks, no titles.
- Do not address Magnus directly. Do not name yourself.
- Lines must fit within ~30 characters each — the screen is small.

Output exactly three lines. No preamble, no commentary."""


@dataclass
class VerseContext:
    when: datetime
    weather_summary: Optional[str] = None  # e.g. "14° clear"
    project_note: Optional[str] = None  # e.g. "magnus is shipping skald today"
    recent_verses: list[list[str]] = None  # last few, to avoid repetition

    def to_user_prompt(self) -> str:
        when = self.when
        hour = when.hour
        if 5 <= hour < 9:
            time_of_day = "early morning"
        elif 9 <= hour < 12:
            time_of_day = "late morning"
        elif 12 <= hour < 14:
            time_of_day = "midday"
        elif 14 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 21:
            time_of_day = "evening"
        elif 21 <= hour < 24:
            time_of_day = "night"
        else:
            time_of_day = "small hours"
        parts = [
            f"It is {time_of_day} — {when.strftime('%A %-d %B %Y, %H:%M')}.",
        ]
        if self.weather_summary:
            parts.append(f"Outside: {self.weather_summary}.")
        if self.project_note:
            parts.append(f"Quiet context: {self.project_note}")
        if self.recent_verses:
            recent = "\n".join("  " + " / ".join(v) for v in self.recent_verses[:4])
            parts.append(f"Recent verses (do not repeat phrasings or images):\n{recent}")
        parts.append("Write the verse.")
        return "\n\n".join(parts)


FALLBACK_VERSES: list[list[str]] = [
    ["the small lamp is patient,", "the page does not hurry —", "outside, a bird begins."],
    ["snow on the windowsill,", "the kettle finds its tune,", "the day waits to be named."],
    ["a clean cup, a closed book,", "the radiator hums low —", "morning has not chosen yet."],
    ["wind reads the spruce again,", "rewrites the same sentence —", "we keep its rough draft."],
    ["the afternoon light leans west,", "the keys cool under both hands,", "we begin once more, gently."],
    ["lamp on, lamp off, lamp on —", "the dusk learning your habits,", "or you learning the dusk."],
    ["one small task, one warm room,", "the rest of the world held back,", "for an hour, by good doors."],
    ["evening folds itself small,", "the screen keeps its own counsel,", "outside, the maples breathe."],
]


def _pick_fallback(seed: int) -> list[str]:
    rng = random.Random(seed)
    return list(rng.choice(FALLBACK_VERSES))


def compose(ctx: VerseContext) -> tuple[list[str], str, bool]:
    """Compose a three-line verse.

    Returns (lines, source, stale).
    source: "claude-haiku-4-5" or "fallback".
    stale: True if we fell back.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        seed = int(ctx.when.timestamp()) // 3600
        return _pick_fallback(seed), "fallback", True

    try:
        from anthropic import Anthropic
    except Exception:
        seed = int(ctx.when.timestamp()) // 3600
        return _pick_fallback(seed), "fallback", True

    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": ctx.to_user_prompt()}],
            temperature=0.95,
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text").strip()
    except Exception:
        seed = int(ctx.when.timestamp()) // 3600
        return _pick_fallback(seed), "fallback", True

    lines = [_clean_line(line) for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        seed = int(ctx.when.timestamp()) // 3600
        return _pick_fallback(seed), "fallback", True
    lines = lines[:3]
    # Enforce line length (~30 chars) — if anything's wildly over, fall back.
    if any(len(line) > 36 for line in lines):
        seed = int(ctx.when.timestamp()) // 3600
        return _pick_fallback(seed), "fallback", True
    return lines, MODEL, False


def _clean_line(line: str) -> str:
    line = line.strip()
    # Strip stray quotation marks, list markers, leading numbers
    if line and line[0] in "\"'“‘":
        line = line[1:]
    if line and line[-1] in "\"'”’":
        line = line[:-1]
    for prefix in ("- ", "* ", "1. ", "2. ", "3. ", "1) ", "2) ", "3) "):
        if line.startswith(prefix):
            line = line[len(prefix):]
            break
    return line.strip()
