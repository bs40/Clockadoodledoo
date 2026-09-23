"""Times of day as "HH:MM" strings, and daily windows that may span midnight."""
from datetime import time


def parse_hhmm(s):
    h, m = s.split(":")
    return time(int(h) % 24, int(m) % 60)


def in_window(t, start, end):
    """Is time-of-day `t` inside [start, end)? A window with start > end spans midnight."""
    a, b = parse_hhmm(start), parse_hhmm(end)
    if a == b:
        return False
    return a <= t < b if a < b else (t >= a or t < b)


def step_hhmm(s, minutes):
    h, m = s.split(":")
    total = (int(h) * 60 + int(m) + minutes) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"
