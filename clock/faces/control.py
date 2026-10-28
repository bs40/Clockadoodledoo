"""Spaceship control-room poster face: date, time and a weather table beside a big window onto
the Earth, two crew at their consoles, and a column of flight readings.

The backgrounds come from retro_space_clock_03_control_room.png via tools/prep_control.py.
The flight readings tell a little story: a crew of three, the altitude rising and falling a
couple of kilometres over each 92-minute orbit (the velocity a touch the other way) and the
minutes counting down to the next orbit, all worked out from the clock so they carry on across
restarts. Animation: the console screens glow and pulse, the console lamps blink, a sweep turns
on the round orange scope, the star by the moon and faint stars in the window twinkle, a meteor
now and then, and the colon blinks on odd seconds.
"""
import math

import pygame

from .. import ui
from .artwork import ArtworkFace, Flicker, Lamps, Meteor, Sparkles, Twinkle, mapper

CREAM = (250, 241, 206)
WHITE = (247, 242, 222)
STARLIGHT = (236, 240, 255)
TEAL = (90, 230, 220)
RED = (255, 70, 40)
AMBER = (255, 170, 60)
LAMP = (255, 236, 196)

ORBIT = 92 * 60                                             # seconds per orbit

POSTER = mapper((0, 0, 2000, 848), (0, 21, 1600, 678.4))     # landscape: the letterboxed poster
WINDOW = mapper((596, 28, 800, 792), (0, 0, 720, 713))      # portrait: same pieces as prep_control.py
TABLE = mapper((55, 316, 432, 294), (14, 1020, 432, 294))
COLUMN = mapper((1746, 56, 232, 558), (474, 1020, 232, 558))
CONSOLE = mapper((296, 649, 290, 166), (14, 1330, 432, 248))

# In poster pixels: screens (rect, kind), lamps (x, y, colour), the scope (x, y, radius).
SCREENS = (((40, 655, 270, 790), "teal"), ((335, 655, 575, 793), "teal"), ((1660, 648, 1860, 760), "teal"),
           ((1490, 648, 1610, 725), "paper"))
LAMP_SPOTS = ((518, 809, RED), (532, 808, AMBER), (460, 809, AMBER), (1057, 630, AMBER), (1118, 630, LAMP),
              (1897, 712, AMBER), (1948, 752, AMBER), (1955, 657, LAMP), (933, 633, LAMP), (1016, 710, LAMP))
SCOPE = (981, 672, 38)
STAR = (765, 162)                                           # the sparkle star by the moon
SPECK = (1011, 112)                                         # and a little one above it
WINDOW_SKY = (705, 75, 1650, 515)
METEOR_SKY = (712, 78, 962, 308)


def _rect(m, x0, y0, x1, y1):
    (a, b), (c, d) = m(x0, y0), m(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _readout(m, k, x, y, cap, max_w):
    """A readout at poster (x, y) placed through mapping m (poster pixels scaled by k)."""
    return m(x, y) + (cap * k, max_w * k)


def _layout(pieces, screen):
    """Effect positions for one orientation. pieces are (mapping, scale, (x0, y0, x1, y1)): where
    the poster's pixels inside that box land on the canvas; the first holds the window and the
    scope. The stars stay within `screen`."""
    def place(x0, y0, x1=None, y1=None):
        for m, k, (a, b, c, d) in pieces:
            if a <= x0 <= c and b <= y0 <= d and (x1 is None or (a <= x1 <= c and b <= y1 <= d)):
                return m
    m, k = pieces[0][:2]
    return dict(
        screens=tuple((_rect(place(*r), *r), kind) for r, kind in SCREENS if place(*r)),
        lamps=tuple(place(x, y)(x, y) + (colour,) for x, y, colour in LAMP_SPOTS if place(x, y)),
        scope=m(*SCOPE[:2]) + (round(SCOPE[2] * k),),
        sparkles=(m(*STAR) + (round(34 * k),), m(*SPECK) + (round(12 * k),)),
        stars=_rect(m, *WINDOW_SKY).clip(screen), avoid=(pygame.Rect(m(*STAR)[0] - 30, m(*STAR)[1] - 30, 60, 60),),
        meteor=_rect(m, *METEOR_SKY),
    )


def _rows(m, k, x, ys, cap, max_w):
    return [dict(kind=kind, icon=None, value=_readout(m, k, x, y, cap, max_w), label=None)
            for kind, y in zip(("temp", "humidity", "pressure", "wind"), ys)]


VALUE_YS = (366, 434, 502, 571)                             # weather values, poster pixels
FLIGHT = ((1775, 147), (1774, 286), (1774, 426), (1774, 566))   # crew, altitude, velocity, next orbit

LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 21),
        date=(102, 80, 36, 480), time=(103, 204, 152, 530), date_tracking=9,
        rows=_rows(lambda x, y: (x, y), 1, 288, VALUE_YS, 31, 188),
        flight=[(x, y, 30, 180) for x, y in FLIGHT],
        **_layout(((POSTER, 0.8, (0, 0, 2000, 848)),), pygame.Rect(0, 0, 1600, 720)),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 765, 38, 640, "center"), time=(360, 893, 166, 640, "center"), date_tracking=9,
        rows=_rows(TABLE, 1, 288, VALUE_YS, 31, 188),
        flight=[_readout(COLUMN, 1, x, y, 30, 180) for x, y in FLIGHT],
        **_layout(((WINDOW, 0.9, (596, 28, 1396, 820)), (CONSOLE, 1.49, (296, 649, 586, 815))),
                  pygame.Rect(0, 0, 720, 713)),
    ),
}


def _teal(r, g, b):
    """A screen's glowing lines and dials."""
    return g > 60 and b > 55 and r < g * 0.8


def _paper(r, g, b):
    """A pale read-out screen."""
    return r > 150 and g > 140 and b > 100


def _sky(r, g, b):
    return r < 40 and g < 60 and b < 80


class Sweep:
    """A radar sweep turning on a round scope at (x, y, radius): a bright line with a fading
    trail, added to the picture. The turns are drawn once, up front."""
    FRAMES, TRAIL = 120, 70          # turn steps; trail length in degrees

    def __init__(self, scope, colour, period=6.0, strength=0.6):
        x, y, radius = scope
        self.centre, self.period = (x, y), period
        k = 3
        side = (radius * 2 + 2) * k
        c = side / 2
        base = pygame.Surface((side, side))
        for step in range(self.TRAIL, -1, -2):        # oldest, dimmest wedges first
            f = strength * (1 - step / self.TRAIL) ** 1.5
            a0, a1 = math.radians(-step - 2), math.radians(-step)
            points = [(c, c)] + [(c + math.cos(a) * radius * k, c + math.sin(a) * radius * k)
                                 for a in (a0, (a0 + a1) / 2, a1)]
            pygame.draw.polygon(base, tuple(int(v * f) for v in colour), points)
        pygame.draw.line(base, tuple(int(v * min(strength * 1.5, 1)) for v in colour), (c, c), (c + radius * k, c), k * 3 // 2)
        base = pygame.transform.smoothscale(base, (side // k, side // k))
        self.frames = [pygame.transform.rotate(base, -360 * i / self.FRAMES) for i in range(self.FRAMES)]

    def draw(self, surf, t):
        frame = self.frames[int((t % self.period) / self.period * self.FRAMES)]
        surf.blit(frame, frame.get_rect(center=self.centre), special_flags=pygame.BLEND_RGB_ADD)


class ControlFace(ArtworkFace):
    name = "control"
    folder = "control"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = WHITE
    TIME_INK = CREAM

    def extra_static(self, surf, now, readings):
        """The flight readings in the right-hand column."""
        ts = now.timestamp()
        swing = math.sin(2 * math.pi * (ts % ORBIT) / ORBIT)
        values = ("3", f"{408 + 2 * swing:.0f} km", f"{7.66 - 0.01 * swing:.2f} km/s",
                  f"{ORBIT // 60 - int(ts // 60) % (ORBIT // 60)} min")
        for value, spec in zip(values, self.L["flight"]):
            self.put(surf, value, spec, ui.LABEL_MED, self.INK, tracking=1, distress=4)

    def make_effects(self):
        L = self.L
        screens = [Flicker(self.art, rect, _teal if kind == "teal" else _paper,
                           TEAL if kind == "teal" else LAMP, amount=0.22, speed=0.3, seed=7 + i, steady=0.2)
                   for i, (rect, kind) in enumerate(L["screens"])]
        return screens + [
            Sweep(L["scope"], (255, 214, 150)),
            Twinkle(self.art, L["stars"], 36, _sky, STARLIGHT, seed=13, avoid=L["avoid"]),
            Sparkles(L["sparkles"], STARLIGHT),
            Meteor(self.art, L["meteor"], (L["meteor"].left + 30, L["meteor"].right - 20), STARLIGHT,
                   (L["meteor"].top + 10, L["meteor"].top + L["meteor"].height // 2)),
            Lamps([(x, y, 6, colour, period, duty) for (x, y, colour), period, duty
                   in zip(L["lamps"], (2.2, 3.1, 1.7, 2.6, 4.0, 1.9, 3.4, 2.8, 3.7, 2.4),
                          (0.5, 0.35, 0.6, 0.4, 0.55, 0.3, 0.45, 0.6, 0.4, 0.5))]),
        ]
