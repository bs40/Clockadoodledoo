"""Mars-colony poster face: date, time and weather down the left beside a chrome robot looking
out over a red planet, its canyons and a domed colony.

The backgrounds come from retro_space_clock_04_robot_colony.png via tools/prep_colony.py.
Animation: the robot's eyes glow softly and its antenna bulb blinks, faint stars twinkle in the
upper sky, the colony's tower tips blink and its dome windows glow, every so often a meteor
streaks across the sky, and the colon blinks on odd seconds. (Dust drifting over the ground was
tried and dropped: it doesn't show on the bright sand.)
"""
import math

import pygame

from .artwork import ArtworkFace, Flicker, Lamps, Meteor, Twinkle, _glow, mapper

CREAM = (247, 240, 218)
LABEL = (236, 224, 196)
AMBER = (248, 184, 92)
TAN = (226, 166, 112)
EYE = (255, 110, 50)
BULB = (255, 120, 90)
BEACON = (255, 214, 150)
RED = (255, 70, 45)

# Effects are placed in poster pixels (the mockup 2000 px wide) and mapped onto each canvas.
LAND = mapper((0, 0, 2000, 846), (0, 22, 1600, 677))               # the letterboxed poster
ROBOT = mapper((552, 18, 860, 812), (0, 0, 720, 680))              # portrait: same piece as prep_colony.py


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _rows(icon_x, value_x, ys, icon_dy, size, caps, label_cap, max_w):
    """The four weather rows; each label sits just below its value, whatever the value's size."""
    return [dict(kind=kind, icon=(icon_x, y + icon_dy, size),
                 value=(value_x, y, cap, max_w), label=(value_x, y + cap // 2 + 29, label_cap, max_w))
            for kind, y, cap in zip(("temp", "humidity", "pressure", "wind"), ys, caps)]


def _effects(to):
    """Positions of the animations through the point mapping `to`."""
    return dict(
        eyes=_rect(to, 700, 112, 850, 162),
        eye_glows=[to(731, 136) + (9,), to(767, 133) + (9,), to(829, 131) + (13,)],
        lamps=[to(x, y) + (r, colour, period, duty) for x, y, r, colour, period, duty in (
            (867, 164, 9, BULB, 2.8, 0.45), (770, 25, 5, BULB, 4.1, 0.3),            # the robot's bulbs
            (1391, 362, 7, BEACON, 2.2, 0.35), (1345, 463, 6, BEACON, 3.1, 0.3),     # tower tips
            (1446, 568, 5, BEACON, 2.6, 0.4), (1879, 300, 7, RED, 3.6, 0.3))],
        windows=_rect(to, 1600, 618, 1800, 672),
    )


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 22),
        date=(87, 78, 34, 520), time=(84, 202, 156, 520),
        rows=_rows(130, 241, (352, 480, 604, 724), 15, 112, (50, 43, 42, 42), 22, 380),
        stars=_rect(LAND, 30, 20, 1990, 175),
        avoid=(_rect(LAND, 30, 20, 640, 310), _rect(LAND, 680, 0, 900, 320), _rect(LAND, 1400, 10, 1575, 185),
               _rect(LAND, 1590, 0, 1725, 400), _rect(LAND, 1715, 40, 1960, 240)),
        sky=_rect(LAND, 880, 18, 1405, 190), meteor_x=(LAND(960, 0)[0], LAND(1330, 0)[0]),
        **_effects(LAND),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 772, 32, 600, "center"), time=(360, 900, 150, 620, "center"),
        rows=_rows(112, 208, (1052, 1178, 1304, 1430), 12, 94, (46, 42, 42, 42), 20, 430),
        texts=(("NEW FRONTIERS  ·  SAME CURIOSITY", (360, 1543, 20, 600, "center"), TAN, 7),),
        stars=pygame.Rect(0, 0, 720, 150), avoid=(_rect(ROBOT, 680, 0, 900, 320),),
        sky=_rect(ROBOT, 880, 18, 1412, 190), meteor_x=(ROBOT(960, 0)[0], ROBOT(1330, 0)[0]),
        **_effects(ROBOT),
    ),
}


def _night(r, g, b):
    return r < 60 and g < 55 and b < 70


def _eye(r, g, b):
    """The red-orange lenses of the robot's eyes, not its cream and steel head."""
    return r > 110 and r - b > 80 and g < 170


def _window(r, g, b):
    """The orange lit windows inside the big dome, not its cream frame."""
    return r > 170 and g < 170 and b < 95 and r - b > 110


class Pulse(Flicker):
    """A Flicker that breathes slowly and smoothly instead of wavering."""

    def __init__(self, *args, period=4.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.period = period

    def level(self, t):
        wave = 0.5 - 0.5 * math.cos(2 * math.pi * (t / self.period + self.phase))
        return self.steady + (1 - self.steady) * wave


class Glows:
    """Soft lights added over the picture that brighten and dim together: (x, y, radius)."""
    LEVELS = 12

    def __init__(self, points, colour, period=4.0, low=0.25, phase=0.0):
        self.period, self.low, self.phase = period, low, phase
        self.lights = []
        for x, y, r in points:
            sprite = _glow(r, colour)
            frames = []
            for level in range(1, self.LEVELS + 1):            # black-backed, for adding on
                frame = pygame.Surface(sprite.get_size())
                faded = sprite.copy()
                faded.fill((255, 255, 255, int(255 * level / self.LEVELS)), special_flags=pygame.BLEND_RGBA_MULT)
                frame.blit(faded, (0, 0))
                frames.append(frame)
            self.lights.append((frames, frames[0].get_rect(center=(x, y))))

    def draw(self, surf, t):
        wave = 0.5 - 0.5 * math.cos(2 * math.pi * (t / self.period + self.phase))
        level = int((self.low + (1 - self.low) * wave) * self.LEVELS + 0.5)
        if level:
            for frames, rect in self.lights:
                surf.blit(frames[min(level, self.LEVELS) - 1], rect, special_flags=pygame.BLEND_RGB_ADD)


class ColonyFace(ArtworkFace):
    name = "colony"
    folder = "colony"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = CREAM
    LABEL_INK = LABEL
    ICON_INK = {"temp": AMBER}

    def make_effects(self):
        L = self.L
        on = pygame.Rect((0, 0), L["size"])
        eyes = Pulse(self.art, L["eyes"], _eye, EYE, amount=0.6, period=4.5)
        effects = [
            Twinkle(self.art, L["stars"], 36, _night, CREAM, seed=13, avoid=L["avoid"]),
            Meteor(self.art, L["sky"], L["meteor_x"], CREAM),
            eyes,
            Glows(L["eye_glows"], (210, 70, 25), period=eyes.period, phase=eyes.phase, low=0.0),
            Lamps([lamp for lamp in L["lamps"] if on.collidepoint(lamp[:2])], seed=9),
        ]
        if on.contains(L["windows"]):                     # the big dome is off the portrait's piece
            effects.append(Pulse(self.art, L["windows"], _window, (255, 170, 90), amount=0.22, period=7.0, steady=0.3))
        return effects
