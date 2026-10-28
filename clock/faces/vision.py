"""Cosmic-vision psychedelic face: date, time and weather down the left beside a woman in profile,
eyes closed, a starburst blazing at her third eye and a tunnel of faces and glowing orbs
receding into a starry sky with planets.

The backgrounds come from psychedelic_clock_02_cosmic_vision.png via tools/prep_vision.py.
Animation: the third-eye starburst breathes slowly (its glow and rays brighten and fade), the
orbs down the tunnel of faces light up in a slow wave travelling away into the distance, the
four-pointed stars in the sky swell and fade, faint stars twinkle, and the colon blinks on odd
seconds. The lettering has a soft dark halo, as the poster's own does, so it reads over the art.
"""
import math

import pygame

from .. import ui
from .artwork import ArtworkFace, Sparkles, Twinkle, _glow, mapper

PEACH = (243, 192, 126)           # the big digits
CREAM = (244, 206, 140)           # date and values
AMBER = (247, 181, 94)            # icons
STAR = (255, 236, 200)
GLOW = (255, 196, 120)

POSTER = mapper((0, 0, 2000, 878), (0, 9, 1600, 702))      # landscape: poster -> canvas
ART = mapper((740, 16, 760, 840), (0, 0, 720, 796))        # portrait: same piece as prep_vision.py

EYE = (996, 248)                  # the starburst at her third eye, in poster pixels
EYE_BOX = (770, 16, 1250, 470)    # the reach of its rays that brighten with it
# the glowing orbs down the tunnel, nearest first: (x, y, radius of their glow)
ORBS = ((1325, 362, 70), (1478, 415, 56), (1590, 450, 46), (1667, 482, 36), (1727, 493, 29),
        (1767, 507, 23), (1802, 517, 19), (1830, 522, 16))
# the four-pointed stars in the sky: (x, y, size)
SPARKS = ((1819, 72, 30), (1909, 76, 34), (1841, 260, 46), (1928, 163, 15), (1709, 229, 15),
          (1891, 379, 18), (1931, 416, 17))


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _scaled(to, points, k):
    return tuple(to(x, y) + (max(round(r * k), 2),) for x, y, r in points)


def _rows(icon_x, value_x, specs):
    """specs: (kind, icon y, icon size, value y, value cap, max width) per row."""
    return [dict(kind=kind, icon=(icon_x, iy, size), value=(value_x, vy, cap, max_w), label=None)
            for kind, iy, size, vy, cap, max_w in specs]


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 9),
        date=(100, 313, 48, 500), date_tracking=17, time=(84, 158, 182, 650),
        rows=_rows(130, 231, (
            ("temp", 419, 110, 422, 56, 420),
            ("humidity", 527, 100, 532, 55, 300),
            ("pressure", 638, 102, 640, 55, 300),
            ("wind", 752, 104, 751, 56, 300),
        )),
        eye=POSTER(*EYE) + (round(95 * 0.8),), eye_box=_rect(POSTER, *EYE_BOX),
        orbs=_scaled(POSTER, ORBS, 0.8), sparks=_scaled(POSTER, SPARKS, 0.8),
        stars=_rect(POSTER, 1500, 20, 1985, 480),
        avoid=(_rect(POSTER, 1535, 15, 1745, 200), _rect(POSTER, 1760, 175, 1925, 345)),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        time=(360, 980, 150, 640, "center"), date=(360, 1108, 38, 600, "center"), date_tracking=14,
        rows=_rows(178, 262, (
            ("temp", 1222, 92, 1222, 46, 400),
            ("humidity", 1316, 84, 1316, 46, 400),
            ("pressure", 1410, 86, 1410, 46, 400),
            ("wind", 1504, 88, 1504, 46, 400),
        )),
        eye=ART(*EYE) + (round(95 * 720 / 760),), eye_box=_rect(ART, *EYE_BOX),
        orbs=_scaled(ART, ORBS[:2], 720 / 760), sparks=(),
        stars=None, avoid=(),
    ),
}


def _night(r, g, b):
    """The dark blue starry sky (not the planets, the tunnel or the stars)."""
    return r < 45 and g < 60 and b < 85


class Breath:
    """The third-eye starburst breathing: the bright parts of `rect` (the blazing core and its
    rays) and a soft glow around `centre` are added over the picture, swelling and fading
    slowly; `amount` is the strongest. The light layer is made once, at a few strengths, with
    blits only."""
    LEVELS = 14

    def __init__(self, art, rect, centre, radius, colour, period=7.0, low=0.1, amount=0.65, floor=185):
        self.rect, self.period, self.low = rect, period, low
        light = art.subsurface(rect).copy()
        light.fill((floor,) * 3, special_flags=pygame.BLEND_RGB_SUB)       # only what is bright
        for _ in range(2):                                                  # x4
            light.blit(light.copy(), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        w, h = rect.size
        bloom = pygame.transform.smoothscale(pygame.transform.smoothscale(light, (max(w // 8, 1), max(h // 8, 1))), (w, h))
        light.blit(bloom, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        halo = _glow(radius, colour)
        glow = pygame.Surface(halo.get_size())
        glow.blit(halo, (0, 0))
        light.blit(glow, glow.get_rect(center=(centre[0] - rect.x, centre[1] - rect.y)), special_flags=pygame.BLEND_RGB_ADD)
        self.frames = []
        for level in range(1, self.LEVELS + 1):
            frame = light.copy()
            v = round(255 * amount * level / self.LEVELS)
            frame.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            self.frames.append(frame)

    def level(self, t):
        wave = 0.5 - 0.5 * math.cos(2 * math.pi * t / self.period)
        return self.low + (1 - self.low) * wave ** 1.5

    def draw(self, surf, t):
        level = int(self.level(t) * self.LEVELS + 0.5)
        if level:
            surf.blit(self.frames[min(level, self.LEVELS) - 1], self.rect, special_flags=pygame.BLEND_RGB_ADD)


class OrbWave:
    """The orbs down the tunnel light up one after another, a slow wave of light travelling away
    into the distance every `period` seconds. orbs: (x, y, radius), nearest first."""
    LEVELS = 10

    def __init__(self, orbs, colour, period=9.0, step=0.45, rise=1.6, low=0.1):
        self.period, self.step, self.rise, self.low = period, step, rise, low
        self.orbs = []
        for x, y, r in orbs:
            sprite = _glow(r, colour)
            frames = []
            for level in range(1, self.LEVELS + 1):               # black-backed, for adding on
                frame = pygame.Surface(sprite.get_size())
                faded = sprite.copy()
                faded.fill((255, 255, 255, int(255 * level / self.LEVELS)), special_flags=pygame.BLEND_RGBA_MULT)
                frame.blit(faded, (0, 0))
                frames.append(frame)
            self.orbs.append((frames, frames[0].get_rect(center=(x, y))))

    def level(self, t, i):
        k = ((t - i * self.step) % self.period) / self.rise        # 0..1 while this orb is lit
        lit = math.sin(math.pi * k) ** 2 if k < 1 else 0.0
        return self.low + (1 - self.low) * lit

    def draw(self, surf, t):
        for i, (frames, rect) in enumerate(self.orbs):
            level = int(self.level(t, i) * self.LEVELS + 0.5)
            if level:
                surf.blit(frames[min(level, self.LEVELS) - 1], rect, special_flags=pygame.BLEND_RGB_ADD)


def _halo(text, spread, strength):
    """A soft dark shadow of `text` (a surface with alpha), `spread` px beyond it each side."""
    w, h = text.get_size()
    sil = pygame.Surface((w + spread * 2, h + spread * 2), pygame.SRCALPHA)
    sil.blit(text, (spread, spread))
    sil.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MIN)          # black, same alpha
    sil = pygame.transform.gaussian_blur(sil, max(spread // 2, 1))
    sil.fill((255, 255, 255, strength), special_flags=pygame.BLEND_RGBA_MULT)
    return sil


class VisionFace(ArtworkFace):
    name = "vision"
    folder = "vision"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = CREAM
    TIME_INK = PEACH
    ICON_INK = {kind: AMBER for kind in ("temp", "humidity", "pressure", "wind")}
    TIME_FONT = "Fraunces72ptSuperSoft-Black"
    DATE_FONT = ui.LABEL_MED
    VALUE_FONT = ui.LABEL_MED
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False
    HALO = 200                    # how dark the lettering's soft shadow is (0-255)

    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        """As ArtworkFace.put, over a soft dark halo like the poster's lettering."""
        x, y, cap, max_w, *anchor = spec
        t = ui.text_fit(s, font, self.S(cap), colour, self.S(max_w), tracking=tracking)
        rect = t.get_rect(**{anchor[0] if anchor else "midleft": self.P(x, y)})
        spread = max(self.S(cap) // 3, 4)
        surf.blit(_halo(t, spread, self.HALO), (rect.x - spread, rect.y - spread))
        surf.blit(t, rect)
        return rect

    def _render_time(self, surf, now):
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        super()._render_time(layer, now)
        box = layer.get_bounding_rect()
        spread = max(self.S(self.L["time"][2]) // 6, 6)
        digits = layer.subsurface(box)
        surf.blit(_halo(digits, spread, self.HALO), (box.x - spread, box.y - spread))
        surf.blit(digits, box)

    def make_effects(self):
        L = self.L
        x, y, radius = L["eye"]
        effects = [
            Breath(self.art, L["eye_box"].clip(self.art.get_rect()), (x, y), radius, GLOW),
            OrbWave(L["orbs"], GLOW),
        ]
        if L["stars"]:
            effects.append(Twinkle(self.art, L["stars"], 34, _night, STAR, seed=21, avoid=L["avoid"]))
        if L["sparks"]:
            effects.append(Sparkles(L["sparks"], STAR, seed=5))
        return effects
