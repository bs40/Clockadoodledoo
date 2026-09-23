"""Small vector icons, drawn 4x oversize and scaled down so edges are smooth."""
import math

import pygame

SS = 4
CLEAR = (0, 0, 0, 0)
_cache = {}


def _stroke(surf, color, pts, w):
    """Polyline with round joins and caps."""
    pts = [(int(x), int(y)) for x, y in pts]
    if len(pts) > 1:
        pygame.draw.lines(surf, color, False, pts, w)
    for p in pts:
        pygame.draw.circle(surf, color, p, w // 2)


def _arc_pts(cx, cy, r, a0, a1, steps=14):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


def _sun(surf, s, c, cx=0.5, cy=0.5, k=1.0):
    pygame.draw.circle(surf, c, (int(cx * s), int(cy * s)), int(0.2 * k * s))
    for i in range(8):
        a = math.radians(i * 45)
        _stroke(surf, c, [((cx + 0.31 * k * math.cos(a)) * s, (cy + 0.31 * k * math.sin(a)) * s),
                          ((cx + 0.43 * k * math.cos(a)) * s, (cy + 0.43 * k * math.sin(a)) * s)],
                max(int(0.07 * k * s), 2))


def _cloud(surf, s, c, dy=0.0, grow=0.0):
    for x, y, r in ((0.32, 0.58, 0.16), (0.52, 0.46, 0.22), (0.72, 0.58, 0.16)):
        pygame.draw.circle(surf, c, (int(x * s), int((y + dy) * s)), int((r + grow) * s))
    pygame.draw.rect(surf, c, pygame.Rect(int((0.32 - grow) * s), int((0.56 + dy) * s),
                                          int((0.40 + 2 * grow) * s), int((0.18 + grow) * s)))


def _partly(surf, s, c):
    _sun(surf, s, c, 0.36, 0.36, 0.72)
    _cloud(surf, s, CLEAR, 0.1, 0.05)
    _cloud(surf, s, c, 0.1)


def _rain(surf, s, c):
    _cloud(surf, s, c, -0.12)
    for x in (0.32, 0.52, 0.72):
        _stroke(surf, c, [(x * s, 0.74 * s), ((x - 0.08) * s, 0.92 * s)], int(0.07 * s))


def _snow(surf, s, c):
    _cloud(surf, s, c, -0.12)
    for x in (0.32, 0.52, 0.72):
        pygame.draw.circle(surf, c, (int(x * s), int(0.84 * s)), int(0.055 * s))


def _storm(surf, s, c):
    _cloud(surf, s, c, -0.12)
    pygame.draw.polygon(surf, c, [(int(x * s), int(y * s)) for x, y in
                                  ((0.56, 0.68), (0.40, 0.86), (0.50, 0.86),
                                   (0.44, 1.0), (0.64, 0.80), (0.54, 0.80))])


def _fog(surf, s, c):
    for i, (x0, x1) in enumerate(((0.12, 0.78), (0.24, 0.90), (0.12, 0.78), (0.24, 0.90))):
        y = (0.26 + 0.17 * i) * s
        _stroke(surf, c, [(x0 * s, y), (x1 * s, y)], int(0.07 * s))


def _drop(surf, s, c):
    pygame.draw.circle(surf, c, (int(0.5 * s), int(0.62 * s)), int(0.24 * s))
    pygame.draw.polygon(surf, c, [(int(0.5 * s), int(0.08 * s)),
                                  (int(0.285 * s), int(0.51 * s)), (int(0.715 * s), int(0.51 * s))])


def _gauge(surf, s, c):
    _stroke(surf, c, _arc_pts(0.5 * s, 0.54 * s, 0.37 * s, 140, 400, 40), int(0.07 * s))
    _stroke(surf, c, [(0.5 * s, 0.54 * s), (0.68 * s, 0.34 * s)], int(0.07 * s))
    pygame.draw.circle(surf, c, (int(0.5 * s), int(0.54 * s)), int(0.07 * s))


def _wind(surf, s, c):
    w = int(0.07 * s)
    _stroke(surf, c, [(0.08 * s, 0.36 * s), (0.58 * s, 0.36 * s)]
            + _arc_pts(0.58 * s, 0.25 * s, 0.11 * s, 90, -150), w)
    _stroke(surf, c, [(0.08 * s, 0.54 * s), (0.78 * s, 0.54 * s)]
            + _arc_pts(0.78 * s, 0.43 * s, 0.11 * s, 90, -150), w)
    _stroke(surf, c, [(0.08 * s, 0.72 * s), (0.50 * s, 0.72 * s)]
            + _arc_pts(0.50 * s, 0.82 * s, 0.10 * s, -90, 140), w)


def _horizon(surf, s, c, rising):
    _sun(surf, s, c, 0.5, 0.62, 0.9)
    surf.fill(CLEAR, pygame.Rect(0, int(0.62 * s), s, s))
    _stroke(surf, c, [(0.08 * s, 0.68 * s), (0.92 * s, 0.68 * s)], int(0.07 * s))
    tip, base = (0.80, 0.94) if rising else (0.94, 0.80)
    pygame.draw.polygon(surf, c, [(int(0.5 * s), int(tip * s)),
                                  (int(0.38 * s), int(base * s)), (int(0.62 * s), int(base * s))])


_DRAWERS = {
    "sun": _sun, "cloud": _cloud, "partly": _partly, "rain": _rain, "snow": _snow,
    "storm": _storm, "fog": _fog, "drop": _drop, "gauge": _gauge, "wind": _wind,
    "sunrise": lambda surf, s, c: _horizon(surf, s, c, True),
    "sunset": lambda surf, s, c: _horizon(surf, s, c, False),
}


def icon(name, size, color):
    key = (name, size, color)
    if key not in _cache:
        big = pygame.Surface((size * SS, size * SS), pygame.SRCALPHA)
        _DRAWERS[name](big, size * SS, color)
        _cache[key] = pygame.transform.smoothscale(big, (size, size))
    return _cache[key]


def moon(phase, size, lit, dark):
    """Moon disc for a phase in [0, 1): 0 = new, 0.5 = full (northern hemisphere view)."""
    key = ("moon", round(phase, 2), size, lit, dark)
    if key not in _cache:
        s = size * SS
        r = s * 0.42
        big = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.circle(big, dark, (s // 2, s // 2), int(r))
        k = math.cos(2 * math.pi * phase)
        for row in range(int(-r), int(r) + 1):
            w = math.sqrt(max(r * r - row * row, 0))
            x0, x1 = (w * k, w) if phase < 0.5 else (-w, -w * k)
            if x1 - x0 >= 1:
                pygame.draw.line(big, lit, (int(s / 2 + x0), s // 2 + row), (int(s / 2 + x1), s // 2 + row))
        _cache[key] = pygame.transform.smoothscale(big, (size, size))
    return _cache[key]
