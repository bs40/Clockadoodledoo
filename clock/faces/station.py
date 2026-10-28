"""Orbital-station poster face: date, time and weather over a banded planet's shadow side, a
rocket ship and a wheel station in orbit, the other weather values in the top-right table.

The backgrounds come from retro_space_clock_05_orbital_station.png via tools/prep_station.py.
Animation: the ship's engine flames flicker and waver, beacons blink on the station and the
ship, faint stars twinkle, an occasional meteor crosses the sky and the colon blinks on odd
seconds.
"""
import pygame

from .artwork import ArtworkFace, Flicker, Lamps, Meteor, Ripple, Twinkle, mapper

CREAM = (248, 241, 210)
SUN = (247, 194, 102)
RED = (255, 60, 40)
AMBER = (255, 176, 70)
GREEN = (120, 255, 150)
STROBE = (255, 240, 215)

LAND = mapper((0, 0, 2000, 880), (0, 8, 1600, 704))           # landscape: the whole poster
SHIP = mapper((45, 452, 860, 286), (0, 0, 720, 239))           # portrait: same pieces as
STATION = mapper((960, 178, 660, 622), (0, 239, 720, 679))     # prep_station.py

FLAMES = (50, 500, 372, 700)            # the ship's two engine flames, in poster pixels
TAILS = (52, 505, 236, 700)             # their outer parts, which waver
LAMPS = (                               # (x, y, colour, period, duty), in poster pixels
    (452, 463, STROBE, 1.7, 0.12), (858, 668, GREEN, 3.1, 0.25),                # the ship's fin and nose
    (561, 490, RED, 3.4, 0.3), (1487, 176, RED, 2.6, 0.35),                    # the station's truss and mast,
    (1538, 346, AMBER, 1.9, 0.3), (1449, 368, AMBER, 2.3, 0.3), (1487, 842, GREEN, 2.9, 0.3),   # aerials, foot
)


def _rect(m, x0, y0, x1, y1):
    """Poster box corners -> canvas rect, through a mapper."""
    (a, b), (c, d) = m(x0, y0), m(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _lamps(m, inside=None):
    """The lamps inside `inside` (a poster rect: a portrait piece), mapped onto the canvas."""
    return tuple((*m(x, y), colour, period, duty) for x, y, colour, period, duty in LAMPS
                 if inside is None or pygame.Rect(inside).collidepoint(x, y))


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 8),
        date=(103, 74, 38, 470), date_tracking=8, time=(103, 204, 172, 540),
        rows=[dict(kind="temp", icon=(150, 381, 104), value=(255, 370, 58, 330), label=(257, 418, 24, 430)),
              dict(kind="humidity", icon=None, value=(1766, 71, 27, 175), label=None),
              dict(kind="pressure", icon=None, value=(1766, 137, 27, 175), label=None),
              dict(kind="wind", icon=None, value=(1766, 203, 27, 175), label=None)],
        stars=_rect(LAND, 40, 20, 1950, 860),
        avoid=(_rect(LAND, 40, 20, 700, 470), _rect(LAND, 1550, 30, 1945, 240), _rect(LAND, 1655, 415, 1945, 765)),
        meteor=_rect(LAND, 1010, 120, 1440, 330),
        flames=_rect(LAND, *FLAMES), tails=_rect(LAND, *TAILS),
        lamps=_lamps(LAND),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 965, 30, 640, "center"), date_tracking=8, time=(360, 1075, 140, 640, "center"),
        rows=[dict(kind="temp", icon=(84, 1212, 84), value=(150, 1194, 46, 540), label=(152, 1240, 21, 520))]
            + [dict(kind=kind, icon=None, value=(205, y, 28, 210), label=(40, y, 22, 150))
               for kind, y in (("humidity", 1335), ("pressure", 1410), ("wind", 1485))],
        stars=pygame.Rect(0, 0, 720, 1600),
        avoid=(pygame.Rect(0, 920, 720, 345), pygame.Rect(0, 1265, 440, 260), pygame.Rect(425, 1262, 290, 335)),
        meteor=_rect(STATION, 1180, 200, 1450, 330),
        flames=_rect(SHIP, *FLAMES), tails=_rect(SHIP, *TAILS),
        lamps=_lamps(SHIP, (45, 452, 860, 286)) + _lamps(STATION, (960, 170, 660, 630)),
    ),
}


def _flame(r, g, b):
    return r > 190 and g > 90 and b < 170 and r - b > 80


def _plume(r, g, b):
    """The whole flame down to its dim red fringe: anything warmer than the night sky."""
    return r > 80 and r > b + 30


def _sky_beside(art, rect, wanted):
    """Ripple's fill: for a flame pixel, the sky just above or below the flame in its column."""
    def fill(x, y):
        x += rect.x
        for dy in range(1, rect.height):
            for yy in (rect.y + y - dy, rect.y + y + dy):
                if rect.top <= yy < rect.bottom and not wanted(*art.get_at((x, yy))[:3]):
                    return art.get_at((x, yy))
        return art.get_at((x, rect.y))
    return fill


def _night(r, g, b):
    return r < 30 and g < 50 and b < 70 and b >= r


class StationFace(ArtworkFace):
    name = "station"
    folder = "station"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = CREAM
    ICON_INK = {"temp": SUN}

    def make_effects(self):
        L = self.L
        meteor = L["meteor"]
        return [
            Ripple(self.art, L["tails"], _plume, _sky_beside(self.art, L["tails"], _plume),
                   axis="y", amplitude=1.5, speed=1.3),
            Flicker(self.art, L["flames"], _flame, (255, 190, 110), amount=0.3, speed=1.4),
            Twinkle(self.art, L["stars"], 45, _night, CREAM, seed=5, avoid=L["avoid"]),
            Meteor(self.art, meteor, (meteor.left + 40, meteor.right - 40), CREAM),
            Lamps([(x, y, 6 if L["scale"] < 1 else 7, colour, period, duty)
                   for x, y, colour, period, duty in L["lamps"]]),
        ]
