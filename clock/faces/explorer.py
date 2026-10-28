"""Distant-world poster face: an astronaut in a bubble helmet on a red planet, with date, time
and weather in the teal sky beside the moon and a spaceplane waiting on the plain.

The backgrounds come from retro_space_clock_06_distant_world.png via tools/prep_explorer.py.
Animation: the star-glint on his visor twinkles and now and then a sweep of light crosses the
glass, faint stars twinkle, the spaceplane's lights blink, the odd meteor streaks past the
moons, and the colon blinks on odd seconds.
"""
import math
import random

import pygame

from .artwork import ArtworkFace, Glint, Lamps, Meteor, Sparkles, Twinkle, mapper
from .cosmonaut import BLINK_HOLD, BLINK_LEVELS, BLINK_OPEN, BLINK_SHUT, _blink_frames, _closure

CREAM = (250, 247, 220)
SAND = (247, 225, 180)            # the big digits
LABEL = (236, 232, 202)
AMBER = (246, 196, 103)
SLOGAN = (233, 226, 195)
BEACON = (255, 96, 64)
STROBE = (255, 250, 235)

POSTER = mapper((0, 0, 2000, 878), (0, 9, 1600, 702))       # landscape: poster -> canvas
ASTRO = mapper((20, 16, 886, 838), (0, 0, 720, 681))         # portrait: same piece as prep_explorer.py

# the inside of the helmet's bubble, in poster pixels
VISOR = ((258, 112), (358, 62), (467, 53), (550, 66), (633, 112), (683, 187), (700, 270), (692, 353),
         (658, 420), (608, 474), (545, 515), (430, 500), (300, 470), (250, 440), (192, 353), (187, 270),
         (200, 187))
GLINT = (643, 213)                # the star of light on his visor
# His eye (the one we can see), in poster pixels, as cosmonaut.py's EYES: `top` is the lower edge
# of the lash line, `open` the upper edge of the eye, `shut` the lower lid; `skin` is where to
# sample the lid's colour; `lash` the liner's thickness in poster pixels.
EYE = {"top": ((373, 238), (381, 235), (391, 233), (401, 233), (410, 236), (418, 241), (424, 249)),
       "open": ((374, 240), (382, 237), (391, 236), (401, 236), (410, 238), (417, 243), (423, 251)),
       "shut": ((374, 240), (382, 246), (391, 250), (401, 251), (410, 252), (417, 253), (423, 251)),
       "skin": (396, 227), "lash": 2.5}


def _eye(to_canvas, k):
    """EYE through a poster -> canvas mapping that scales by k."""
    return {"top": [to_canvas(*p) for p in EYE["top"]], "open": [to_canvas(*p) for p in EYE["open"]],
            "shut": [to_canvas(*p) for p in EYE["shut"]], "skin": to_canvas(*EYE["skin"]), "lash": EYE["lash"] * k}


def _rows(icon_x, value_x, specs):
    """specs: (kind, icon y, icon size, value y, value cap, label y, label cap, max width) per row."""
    return [dict(kind=kind, icon=(icon_x, iy, size), value=(value_x, vy, cap, max_w),
                 label=(value_x, ly, label_cap, max_w))
            for kind, iy, size, vy, cap, ly, label_cap, max_w in specs]


class SoftGlint(Glint):
    """Glint with a soft-edged band: the light fades in and out across its width instead of
    stepping, which reads as a reflection gliding over the glass. The slanted band is drawn once
    and slid across the visor."""

    def __init__(self, rect, shape, colour=(255, 250, 235), strength=130, width=0.22):
        super().__init__(rect, shape, colour, strength, width)
        w, h = rect.size
        self.lean = round(h * 0.45)
        span = max(round(width * w), 4)
        strip = pygame.Surface((span, 1))
        for x in range(span):
            k = math.sin(math.pi * (x + 0.5) / span) ** 2          # 0 at the edges, 1 mid-band
            k = 0.45 * k + 0.55 * k ** 6                            # a brighter core
            strip.set_at((x, 0), tuple(int(c * k * strength / 255) for c in colour))
        self.band = pygame.Surface((span + self.lean * 2, h))
        for y in range(h):                                          # lean it over: top to the right
            self.band.blit(strip, (round(self.lean * 2 * (1 - y / max(h - 1, 1))), y))

    def draw(self, surf, t):
        if self.next is None or self.next - t > self.EVERY[1]:
            self.next = t + self.rng.uniform(5, self.EVERY[1])
        if self.start is None and t >= self.next:
            self.start, self.next = t, t + self.rng.uniform(*self.EVERY)
        if self.start is None:
            return
        k = (t - self.start) / self.TIME
        if k >= 1 or k < 0:
            self.start = None
            return
        w = self.rect.width
        centre = -0.3 * w + k * 1.6 * w                             # left to right, as Glint
        self.buf.fill((0, 0, 0))
        self.buf.blit(self.band, (round(centre - self.band.get_width() / 2), 0))
        self.buf.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(self.buf, self.rect.topleft, special_flags=pygame.BLEND_RGB_ADD)


class Blink:
    """He blinks every quarter of a minute or so (cosmonaut.py's eyelid, drawn shut in stages)."""
    EVERY = (12.0, 22.0)

    def __init__(self, art, eye):
        self.topleft, self.frames = _blink_frames(art, eye)
        self.next, self.start = None, None
        self.rng = random.Random()

    def draw(self, surf, t):
        if self.next is None or not -5 <= self.next - t <= self.EVERY[1] + 15:
            self.next = t + self.rng.uniform(*self.EVERY)       # first frame, or the clock jumped
        if t >= self.next:
            self.start, self.next = t, t + self.rng.uniform(*self.EVERY)
        if self.start is None:
            return
        if t - self.start > BLINK_SHUT + BLINK_HOLD + BLINK_OPEN:
            self.start = None
            return
        level = min(int(_closure(t - self.start) * BLINK_LEVELS + 0.5), BLINK_LEVELS)
        if level:
            surf.blit(self.frames[level - 1], self.topleft)


def _box(points, pad=6):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return pygame.Rect(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + pad * 2, max(ys) - min(ys) + pad * 2)


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 9),
        date=(1260, 74, 33, 470), date_tracking=7, time=(1258, 187, 137, 470),
        rows=_rows(1301, 1395, (
            ("temp", 314, 78, 311, 42, 349, 15, 440),
            ("humidity", 393, 66, 384, 34, 419, 18, 300),
            ("pressure", 481, 74, 466, 35, 508, 18, 300),
            ("wind", 571, 84, 560, 35, 597, 18, 185),
        )),
        visor=[POSTER(x, y) for x, y in VISOR], eye=_eye(POSTER, 0.8),
        sparkles=(POSTER(*GLINT) + (44,),),
        stars=pygame.Rect(565, 12, 1000, 380),
        avoid=(pygame.Rect(992, 38, 392, 470), pygame.Rect(1400, 50, 170, 165),     # readouts, slogan
               pygame.Rect(684, 45, 300, 296), pygame.Rect(636, 50, 92, 108)),       # moon, crescent
        meteor=(pygame.Rect(565, 12, 430, 230), (600, 950), (20, 90)),
        lamps=((1525, 226, 12, BEACON, 2.6, 0.35), (1153, 541, 9, STROBE, 3.4, 0.12)),   # fin tip, nose
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 765, 30, 600, "center"), date_tracking=8, time=(360, 885, 150, 640, "center"),
        rows=_rows(150, 240, (
            ("temp", 1056, 84, 1040, 44, 1084, 18, 440),
            ("humidity", 1164, 70, 1150, 40, 1192, 18, 440),
            ("pressure", 1272, 76, 1258, 40, 1300, 18, 440),
            ("wind", 1380, 84, 1366, 40, 1408, 18, 440),
        )),
        texts=(("SAME SKIES  ·  DIFFERENT WORLDS", (360, 1478, 20, 600, "center"), SLOGAN, 7),),
        visor=[ASTRO(x, y) for x, y in VISOR], eye=_eye(ASTRO, 720 / 866),
        sparkles=(ASTRO(*GLINT) + (48,),),
        stars=pygame.Rect(0, 690, 720, 800),
        avoid=(pygame.Rect(150, 735, 420, 230), pygame.Rect(95, 1000, 470, 430),     # readouts
               pygame.Rect(70, 1455, 580, 45)),                                    # slogan
        meteor=(pygame.Rect(540, 0, 180, 240), (600, 700), (15, 60)),
        lamps=(),
    ),
}


def _night(r, g, b):
    """Clear teal sky (not the moons, the rock or the plane)."""
    return b > r + 8 and g > r and r < 70 and g < 120


class ExplorerFace(ArtworkFace):
    name = "explorer"
    folder = "explorer"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = CREAM
    TIME_INK = SAND
    LABEL_INK = LABEL
    ICON_INK = {"temp": AMBER}

    def make_effects(self):
        L = self.L
        sky, x_range, y_range = L["meteor"]
        effects = [
            Blink(self.art, L["eye"]),
            Twinkle(self.art, L["stars"], 30, _night, CREAM, seed=17, avoid=L["avoid"]),
            Meteor(self.art, sky, x_range, CREAM, y_range),
            SoftGlint(_box(L["visor"]), L["visor"]),
            Sparkles(L["sparkles"], CREAM),
        ]
        if L["lamps"]:
            effects.append(Lamps(L["lamps"]))
        return effects
