"""Small astronomy helpers that need no network."""
import math
from datetime import datetime, timezone

SYNODIC_MONTH = 29.530588853
KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

_PHASE_NAMES = ("NEW MOON", "WAXING CRESCENT", "FIRST QUARTER", "WAXING GIBBOUS",
                "FULL MOON", "WANING GIBBOUS", "LAST QUARTER", "WANING CRESCENT")


def moon_phase(now_utc):
    """Return (phase 0..1 where 0.5 is full, illuminated fraction 0..1, name)."""
    days = (now_utc - KNOWN_NEW_MOON).total_seconds() / 86400
    phase = (days / SYNODIC_MONTH) % 1.0
    illum = (1 - math.cos(2 * math.pi * phase)) / 2
    name = _PHASE_NAMES[int(phase * 8 + 0.5) % 8]
    return phase, illum, name
