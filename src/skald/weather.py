"""Open-Meteo weather fetch. Free, no API key, plenty good for a small footer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests

# Defaults: Stockholm. Override via SKALD_LAT / SKALD_LON.
DEFAULT_LAT = 59.3293
DEFAULT_LON = 18.0686


@dataclass
class Weather:
    temp_c: float
    code: int  # WMO weather code
    summary: str  # short human-readable, e.g. "clear", "cloudy", "rain"


# Trimmed WMO weather code → short summary
_CODE_SUMMARY = {
    0: "clear",
    1: "mostly clear", 2: "part cloud", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    61: "rain", 63: "rain", 65: "rain",
    71: "snow", 73: "snow", 75: "snow",
    77: "snow", 80: "showers", 81: "showers", 82: "showers",
    85: "snow show", 86: "snow show",
    95: "storm", 96: "storm", 99: "storm",
}


def fetch(lat: Optional[float] = None, lon: Optional[float] = None, timeout: float = 5.0) -> Optional[Weather]:
    lat = lat if lat is not None else float(os.environ.get("SKALD_LAT", DEFAULT_LAT))
    lon = lon if lon is not None else float(os.environ.get("SKALD_LON", DEFAULT_LON))
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
    )
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        cur = r.json().get("current", {})
        code = int(cur.get("weather_code", 0))
        return Weather(
            temp_c=float(cur.get("temperature_2m", 0.0)),
            code=code,
            summary=_CODE_SUMMARY.get(code, "weather"),
        )
    except Exception:
        return None


def footer_line(w: Optional[Weather], extra: Optional[str] = None) -> str:
    """Compose a footer like '14° clear · the watch is clear'."""
    if w is None:
        left = "weather unknown"
    else:
        left = f"{round(w.temp_c)}° {w.summary}"
    right = extra or "the watch is clear"
    # Keep total short enough; truncate right side if needed.
    max_right = 36 - len(left)
    if len(right) > max_right:
        right = right[: max(0, max_right - 1)] + "…"
    return f"{left} · {right}"
