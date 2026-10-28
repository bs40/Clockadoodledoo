"""Rocket-launch poster face: date, time and weather down the left beside a rocket climbing past
the Earth.

The backgrounds come from retro_space_clock_01_rocket_launch.png via tools/prep_launch.py.
Animation: the exhaust flickers, the lens-flare star and faint stars twinkle, the launch tower's
beacons blink and the colon blinks on odd seconds.
"""
import pygame

from .artwork import ArtworkFace, Flicker, Lamps, Sparkles, Twinkle, mapper

CREAM = (250, 245, 222)
AMBER = (246, 190, 100)
BEACON = (255, 70, 40)

ROCKET = mapper((395, 22, 860, 830), (0, 0, 720, 695))      # portrait: same piece as prep_launch.py


def _rows(icon_x, value_x, ys, size, cap, label_cap, label_dy, max_w):
    return [dict(kind=kind, icon=(icon_x, y + label_dy // 2, size * (1.25 if kind == "temp" else 1)),
                 value=(value_x, y, cap, max_w), label=(value_x, y + label_dy, label_cap, max_w))
            for kind, y in zip(("temp", "humidity", "pressure", "wind"), ys)]


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 11),
        date=(107, 92, 38, 480), time=(103, 228, 176, 540),
        rows=_rows(140, 243, (397, 525, 645, 765), 78, 44, 19, 55, 360),
        stars=pygame.Rect(30, 25, 1550, 330), avoid=(pygame.Rect(30, 25, 500, 680), pygame.Rect(1360, 40, 200, 200)),
        sparkles=((826, 203, 40), (826, 77, 12)),
        exhaust=pygame.Rect(330, 420, 540, 280),
        beacons=((1483, 258), (1421, 410), (1572, 515)),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 790, 32, 600, "center"), time=(360, 905, 150, 620, "center"),
        rows=_rows(115, 205, (1040, 1155, 1270, 1385), 70, 42, 19, 48, 440),
        texts=(("HIGHER WORLDS  ·  BRIGHTER DAYS", (360, 1515, 20, 600, "center"), CREAM, 7),),
        stars=pygame.Rect(0, 0, 720, 420), avoid=(),
        sparkles=(ROCKET(1035, 235) + (40,), ROCKET(1032, 96) + (12,)),
        exhaust=pygame.Rect(0, 330, 720, 365),
        beacons=(),
    ),
}


def _flame(r, g, b):
    return r > 200 and g > 100 and b < 160 and r - b > 90


def _night(r, g, b):
    return r < 40 and g < 50 and b < 60


class LaunchFace(ArtworkFace):
    name = "launch"
    folder = "launch"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = CREAM
    ICON_INK = {"temp": AMBER}

    def make_effects(self):
        L = self.L
        return [
            Flicker(self.art, L["exhaust"], _flame, (255, 200, 120), amount=0.3),
            Twinkle(self.art, L["stars"], 40, _night, CREAM, seed=11, avoid=L["avoid"]),
            Sparkles(L["sparkles"], CREAM),
            Lamps([(x, y, 7, BEACON, 2.4, 0.35) for x, y in L["beacons"]]),
        ]
