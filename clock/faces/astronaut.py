"""Astronaut poster face: date, time and weather on the cream panel beside a woman astronaut in
a glass bubble helmet, with a ringed planet, a moon and a domed city behind her.

The backgrounds come from retro_space_clock_02_astronaut.png via tools/prep_astronaut.py.
Animation: now and then a glint of light sweeps across her helmet's glass and she blinks, faint
stars twinkle in the sky, lights in the domed city glow and fade, and the colon blinks on odd
seconds.
"""
import math
import random

import pygame

from .artwork import ArtworkFace, Glint, Lamps, Twinkle, mapper
from .cosmonaut import BLINK_LEVELS, _closure, _smooth

INK = (18, 24, 30)
LABEL = (34, 38, 40)
RED = (192, 48, 32)
SUN = (204, 56, 30)
SLATE = (64, 69, 72)
STAR = (250, 242, 218)
WINDOW = (255, 200, 96)
BEACON = (255, 90, 60)
LASH = (16, 14, 18)

LAND = mapper((0, 0, 2000, 870), (0, 12, 1600, 696))       # landscape: poster -> canvas
ART = mapper((745, 22, 975, 826), (0, 0, 720, 610))       # portrait: same piece as prep_astronaut.py
ART_BOX = pygame.Rect(745, 22, 975, 826)

GLASS = (1066, 330, 222, 252, -25)          # the helmet's glass: an ellipse (centre, radii, tilt)
SKY = (1300, 22, 1985, 600)                 # the sky right of her helmet, in poster pixels
SLOGAN = (1690, 50, 1950, 260)
WINDOWS = ((1728, 638, 22, 10), (1788, 638, 10, 8), (1588, 641, 15, 7),     # round the dome's foot and
           (1666, 539, 9, 6), (1683, 539, 8, 6))                            # under the observatory: x, y, w, h
BEACONS = ((1768, 312, 7, 2.6), (1369, 472, 7, 3.1), (1864, 372, 6, 3.7))     # spire tips: x, y, radius, period

# Her (left-hand, visible) eye in landscape canvas pixels, as for clock/faces/cosmonaut.py: `top`
# is the upper edge of the lashes, `open` their lower edge, `shut` the lower lid.
EYE = {"top": ((809, 258), (815, 252), (822, 248), (830, 245), (838, 243), (846, 242), (854, 242), (861, 246), (866, 256)),
       "open": ((809, 258), (815, 255), (822, 252), (830, 250), (838, 249), (846, 249), (854, 250), (861, 252), (866, 256)),
       "shut": ((809, 258), (815, 261), (822, 263), (830, 265), (838, 266), (846, 266), (854, 265), (861, 262), (866, 256)),
       "lash": 3.0}
BLINK_EVERY = (14.0, 30.0)


def _poster(x, y):
    """Landscape canvas pixels -> poster pixels."""
    return x / 0.8, (y - 12) / 0.8


def _eye(eye, f):
    k = math.dist(f(*_poster(0, 12)), f(*_poster(100, 12))) / 100
    return {"top": [f(*_poster(*p)) for p in eye["top"]], "open": [f(*_poster(*p)) for p in eye["open"]],
            "shut": [f(*_poster(*p)) for p in eye["shut"]], "lash": eye["lash"] * k}


def _ellipse(f, cx, cy, rx, ry, tilt, n=48):
    c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    pts = [(rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return [f(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def _box(f, rect):
    (a, b), (c, d) = f(*rect[:2]), f(*rect[2:])
    return pygame.Rect(a, b, c - a, d - b)


def _rows(icons, value_x, values, label_dy, label_cap, max_ws):
    """icons: (x, y, size) per row; values: (y, cap) per row."""
    return [dict(kind=kind, icon=icon, value=(value_x, y, cap, w), label=(value_x, y + dy, label_cap, w))
            for kind, icon, (y, cap), dy, w in zip(("temp", "humidity", "pressure", "wind"), icons, values, label_dy, max_ws)]


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 12),
        date=(109, 83, 36, 520), date_tracking=7, time=(107, 228, 194, 560),
        rows=_rows(((149, 418, 112), (150, 548, 100), (152, 672, 94), (152, 778, 112)), 258,
                   ((402, 50), (533, 44), (655, 44), (769, 44)), (59, 53, 51, 49), 21, (290, 250, 205, 195)),
        f=LAND, sky=SKY, avoid=(SLOGAN,), windows=WINDOWS, beacons=BEACONS,
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 700, 32, 600, "center"), date_tracking=9, time=(360, 845, 170, 620, "center"),
        rows=_rows(((165, 1025, 96), (165, 1145, 86), (165, 1265, 82), (165, 1385, 96)), 255,
                   ((1010, 46), (1130, 44), (1250, 44), (1370, 44)), (48, 48, 48, 48), 21, (400, 400, 400, 400)),
        texts=(("A CLEANER BRIGHTER TOMORROW", (360, 1500, 24, 600, "center"), RED, 8),),
        f=ART, sky=(1300, 22, 1720, 848), avoid=(), windows=[w for w in WINDOWS if ART_BOX.collidepoint(w[:2])],
        beacons=[b for b in BEACONS if ART_BOX.collidepoint(b[:2])],
    ),
}


def _night(r, g, b):
    return r < 30 and g < 55 and b < 80


class Windows:
    """Lit windows, (x, y, w, h) boxes centred on canvas points, that slowly brighten and fade,
    each in its own time, now and then going out for a while."""

    def __init__(self, windows, colour, seed=8):
        rng, self.windows = random.Random(seed), []
        for x, y, w, h in windows:
            pad = max(w, h)
            sprite = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
            sprite.fill((*colour, 0))
            pygame.draw.rect(sprite, (*colour, 255), (pad, pad, w, h), border_radius=2)
            small = (max(sprite.get_width() // 4, 1), max(sprite.get_height() // 4, 1))
            glow = pygame.transform.smoothscale(pygame.transform.smoothscale(sprite, small), sprite.get_size())
            pygame.draw.rect(glow, (*colour, 210), (pad + 1, pad + 1, max(w - 2, 1), max(h - 2, 1)), border_radius=2)
            self.windows.append((sprite.get_rect(center=(x, y)), glow, rng.uniform(8, 16), rng.uniform(0, 1)))

    def draw(self, surf, t):
        for rect, sprite, period, phase in self.windows:
            level = min(max(0.55 + 0.7 * math.sin(2 * math.pi * (t / period + phase)), 0.0), 1.0)
            if level > 0.02:
                sprite.set_alpha(int(255 * level))
                surf.blit(sprite, rect)


def _lid_frames(art, eye):
    """Pre-render her eyelid at each stage of closing: skin coloured column by column from just
    above the lashes, so the lid's upper edge melts into her face, with the lashes riding down on
    its lower edge. Returns (topleft, [surface, ...])."""
    k = 4
    every = list(eye["top"]) + list(eye["open"]) + list(eye["shut"])
    box = pygame.Rect(min(p[0] for p in every) - 3, min(p[1] for p in every) - 3, 0, 0)
    box.width = max(p[0] for p in every) + 4 - box.x
    box.height = max(p[1] for p in every) + 4 - box.y
    top = _smooth(list(eye["top"]))
    skin = pygame.Surface(box.size)
    for x in range(box.width):
        cx = min(max(box.x + x, top[0][0]), top[-1][0])
        a, b = next(((a, b) for a, b in zip(top, top[1:]) if a[0] <= cx <= b[0]), (top[0], top[-1]))
        y = round(a[1] + (b[1] - a[1]) * (cx - a[0]) / max(b[0] - a[0], 1e-6)) - 3
        px = [art.get_at((box.x + x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-2, -1, 0)]
        colour = tuple(sum(p[c] for p in px) // len(px) for c in range(3))
        pygame.draw.line(skin, colour, (x, 0), (x, box.height))
    skin = pygame.transform.smoothscale(skin, (max(box.width // 8, 1), box.height))    # even out
    skin = pygame.transform.smoothscale(skin, (box.width * k, box.height * k)).convert_alpha()

    def local(points):
        return [((x - box.x) * k, (y - box.y) * k) for x, y in points]

    frames = []
    for level in range(1, BLINK_LEVELS + 1):
        t = level / BLINK_LEVELS
        edge = _smooth([(ox + (sx - ox) * t, oy + (sy - oy) * t)
                        for (ox, oy), (sx, sy) in zip(eye["open"], eye["shut"])])
        n = len(edge) - 1
        taper = [0.25 + 0.75 * math.sin(math.pi * i / n) ** 0.6 for i in range(n + 1)]
        mask = pygame.Surface(skin.get_size(), pygame.SRCALPHA)
        mask.fill((255, 255, 255, 0))
        pygame.draw.polygon(mask, (255, 255, 255, 255), local(top + edge[::-1]))
        crease = [(x, y - eye["lash"] * 2.6 * w) for (x, y), w in zip(edge, taper)]
        pygame.draw.polygon(mask, (215, 200, 200, 255), local(edge + crease[::-1]))   # shade by the lashes
        lid = skin.copy()
        lid.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        band = [(x, y - eye["lash"] * w) for (x, y), w in zip(edge, taper)]       # lashes, tapering
        pygame.draw.polygon(lid, LASH, local(edge + band[::-1]))
        frames.append(pygame.transform.smoothscale(lid, box.size))
    return box.topleft, frames


class Blink:
    """She blinks every 15 to 30 seconds: an eyelid drawn down over her eye and back up."""

    def __init__(self, art, eye):
        self.pos, self.frames = _lid_frames(art, eye)
        self.start, self.next = None, None
        self.rng = random.Random()

    def draw(self, surf, t):
        if self.next is None or not -5 <= self.next - t <= BLINK_EVERY[1] + 15:
            self.next = t + self.rng.uniform(*BLINK_EVERY)       # first frame, or the clock jumped
        if t >= self.next:
            self.start, self.next = t, t + self.rng.uniform(*BLINK_EVERY)
        if self.start is None:
            return
        closure = _closure(t - self.start)
        if closure <= 0.05 and t - self.start > 0.1:
            self.start = None
            return
        level = min(int(closure * BLINK_LEVELS + 0.5), BLINK_LEVELS)
        if level:
            surf.blit(self.frames[level - 1], self.pos)


class AstronautFace(ArtworkFace):
    name = "astronaut"
    folder = "astronaut"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = INK
    LABEL_INK = LABEL
    TIME_INK = RED
    ICON_INK = {"temp": SUN, "humidity": SLATE}

    def make_effects(self):
        L, f = self.L, self.L["f"]
        k = math.dist(f(0, 0), f(100, 0)) / 100
        glass = _ellipse(f, *GLASS)
        return [
            Twinkle(self.art, _box(f, L["sky"]), 36, _night, STAR, seed=12,
                    avoid=[_box(f, r) for r in L["avoid"]]),
            Windows([(*f(x, y), *(max(round(v * k), 2) for v in (w, h))) for x, y, w, h in L["windows"]], WINDOW),
            Lamps([(*f(x, y), r, BEACON, p, 0.35) for x, y, r, p in L["beacons"]], seed=6),
            Blink(self.art, _eye(EYE, f)),
            Glint(pygame.Rect(glass[0], (1, 1)).unionall([pygame.Rect(p, (1, 1)) for p in glass]), glass,
                  strength=85, width=0.13),
        ]
