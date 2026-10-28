"""Ringed-planet poster face: date, time and weather down the left in the dark sky beside a huge
marbled planet with swirling rings, two small moons, orange clouds and black rock spires over a
still lake that mirrors it all.

The backgrounds come from psychedelic_clock_04_ringed_planet.png via tools/prep_rings.py.
Animation: the lake's reflections shimmer, the sparkle stars swell and fade and faint stars
twinkle in the dark sky, the two moons glow softly in turn (in landscape: the portrait's picture
leaves them out), now and then a shooting star crosses the sky above the planet, and the colon
blinks on odd seconds. The lettering has the soft dark halo the poster prints it with.
"""
import math
import random

import pygame

from .artwork import ArtworkFace, Meteor, Sparkles, Twinkle, _glow, mapper

PINK = (245, 158, 154)            # the big digits
DATE_PINK = (244, 162, 158)
CORAL = (244, 140, 108)           # icons and values
STAR = (255, 236, 200)
HALO = (14, 6, 9)

# Effects are placed in poster pixels (the mockup 2000 px wide) and mapped onto each canvas.
LAND = mapper((0, 0, 2000, 846), (0, 22, 1600, 677))             # the letterboxed poster
PLANET = mapper((1010, 12, 880, 806), (0, 0, 720, 659))          # portrait: same piece as prep_rings.py

SPARKLES = ((1268, 40, 20), (1551, 35, 24), (1585, 42, 24), (1755, 243, 22), (1205, 72, 11), (1517, 27, 9))
MOONS = ((810, 259, 62), (877, 385, 37))                          # centre and radius
# The open water below the far shore, which runs down to the left past the black rocks
LAKE = ((380, 772), (560, 748), (740, 730), (1000, 722), (1150, 716), (1162, 669), (1950, 666), (1950, 780),
        (1905, 826), (380, 826))
SKY = (1000, 14, 1950, 420)                                       # where shooting stars fly


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _rows(icon_x, value_x, specs, max_w):
    """specs: (kind, icon y, icon size, value y, value cap) per row; no labels."""
    return [dict(kind=kind, icon=(icon_x, iy, size), value=(value_x, vy, cap, max_w), label=None)
            for kind, iy, size, vy, cap in specs]


def _effects(to, k):
    """Positions of the animations through the point mapping `to`, which scales by k."""
    return dict(
        sparkles=[to(x, y) + (round(s * k),) for x, y, s in SPARKLES],
        moons=[to(x, y) + (round(r * k),) for x, y, r in MOONS],
        lake=[to(x, y) for x, y in LAKE],
        sky=_rect(to, *SKY), meteor_x=(to(1250, 0)[0], to(1700, 0)[0]), meteor_y=(to(0, 30)[1], to(0, 130)[1]),
    )


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 22),
        date=(98, 303, 47, 520), date_tracking=7, time=(57, 150, 186, 700),
        rows=_rows(130, 232, (
            ("temp", 412, 100, 415, 56),
            ("humidity", 525, 118, 530, 53),
            ("pressure", 637, 112, 637, 56),
            ("wind", 745, 110, 746, 56),
        ), 430),
        stars=_rect(LAND, 1150, 12, 1990, 340), avoid=(),
        **_effects(LAND, 0.8),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 735, 36, 600, "center"), date_tracking=10, time=(360, 865, 165, 640, "center"),
        rows=_rows(160, 250, (
            ("temp", 1060, 92, 1063, 50),
            ("humidity", 1188, 108, 1192, 48),
            ("pressure", 1316, 102, 1316, 50),
            ("wind", 1444, 100, 1445, 50),
        ), 430),
        stars=pygame.Rect(0, 0, 720, 330), avoid=(),
        **_effects(PLANET, 720 / 880),
    ),
}


def _night(r, g, b):
    """The clear navy sky between the rings (not the planet, the rings or the moons)."""
    return r < 40 and g < 55 and b < 65 and b >= r


def _halo(surf, radius, colour, strength):
    """A soft dark shadow of the opaque parts of `surf`, the same size."""
    w, h = surf.get_size()
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    shade.fill((*colour, 255))
    shade.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)     # the text's alpha, in `colour`
    small = (max(w // radius, 1), max(h // radius, 1))
    shade = pygame.transform.smoothscale(pygame.transform.smoothscale(shade, small), (w, h))
    shade.fill((255, 255, 255, strength), special_flags=pygame.BLEND_RGBA_MULT)
    return shade


class Shimmer:
    """The lake's reflections waver: the rows of the water (inside `shape`, a polygon in canvas
    pixels) are lifted off the picture and slid sideways by a pixel or two, more in the
    foreground than out by the far shore."""

    def __init__(self, art, shape, amplitude=2.0, speed=1.0):
        xs, ys = [p[0] for p in shape], [p[1] for p in shape]
        self.rect = pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)).clip(art.get_rect())
        self.amp, self.speed = amplitude, speed
        w, h = self.rect.size
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        mask.fill((255, 255, 255, 0))
        pygame.draw.polygon(mask, (255, 255, 255, 255), [(x - self.rect.x, y - self.rect.y) for x, y in shape])
        mask = pygame.transform.smoothscale(pygame.transform.smoothscale(mask, (max(w // 4, 1), max(h // 4, 1))), (w, h))
        self.water = art.subsurface(self.rect).convert_alpha()
        self.water.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        rows = [self.water.subsurface((0, y, w, 1)).get_bounding_rect() for y in range(h)]
        self.rows = [(y, (r.x, y, r.width, 1)) for y, r in enumerate(rows) if r.width]

    def draw(self, surf, t):
        t *= self.speed
        x0, y0, h = self.rect.x, self.rect.y, self.rect.height
        for y, area in self.rows:
            depth = 0.3 + 0.7 * y / h                         # nearer water moves more
            shift = round(self.amp * depth * (math.sin(y * 0.55 - t * 1.9) * 0.6 + math.sin(y * 0.23 + t * 1.3) * 0.4))
            if shift:
                surf.blit(self.water, (x0 + area[0] + shift, y0 + y), area)


class MoonGlow:
    """The moons brighten softly and dim again, each in its own time, with a faint halo."""
    LEVELS = 10

    def __init__(self, art, moons, period=7.0, seed=6):
        rng = random.Random(seed)
        self.moons = []
        for x, y, r in moons:
            pad = round(r * 0.6)
            box = pygame.Rect(x - r - pad, y - r - pad, (r + pad) * 2, (r + pad) * 2).clip(art.get_rect())
            if box.width < r or box.height < r:
                continue
            cx, cy = x - box.x, y - box.y
            disc = pygame.Surface(box.size)                      # the moon's own colours, inside its rim
            disc.blit(art, (0, 0), box)
            edge = pygame.Surface(box.size)
            for i in range(8, 0, -1):                            # a soft-edged disc
                v = int(255 * (9 - i) / 8)
                pygame.draw.circle(edge, (v, v, v), (cx, cy), round(r * (0.86 + 0.02 * i)))
            disc.blit(edge, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            tint = pygame.transform.average_color(art, pygame.Rect(x - r // 2, y - r // 2, r, r))[:3]
            halo = _glow(r + pad, tuple(min(255, int(c * 1.2)) for c in tint))
            frames = []
            for level in range(1, self.LEVELS + 1):
                k = level / self.LEVELS
                frame = pygame.Surface(box.size)               # black, with the halo laid on
                ring = halo.copy()
                ring.fill((255, 255, 255, int(255 * 0.22 * k)), special_flags=pygame.BLEND_RGBA_MULT)
                frame.blit(ring, ring.get_rect(center=(cx, cy)))
                light = disc.copy()                            # and the moon's own light added
                light.fill(tuple(int(255 * 0.2 * k) for _ in range(3)), special_flags=pygame.BLEND_RGB_MULT)
                frame.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                frames.append(frame)
            self.moons.append((frames, box.topleft, rng.uniform(period * 0.8, period * 1.25), rng.uniform(0, 1)))

    def draw(self, surf, t):
        for frames, pos, period, phase in self.moons:
            wave = 0.5 - 0.5 * math.cos(2 * math.pi * (t / period + phase))
            level = int(wave ** 1.5 * self.LEVELS + 0.5)
            if level:
                surf.blit(frames[level - 1], pos, special_flags=pygame.BLEND_RGB_ADD)


class ShootingStar(Meteor):
    """A short, quick meteor now and then, high in the sky; it burns up in the air, so it streaks
    across the rings and the planet too."""
    EVERY = (60.0, 150.0)
    LENGTH, TIME, TRAVEL = 70, 0.8, 220


class RingsFace(ArtworkFace):
    name = "rings"
    folder = "rings"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    TIME_FONT = "Fraunces72ptSuperSoft-Black"
    DATE_FONT = "Jost-SemiBold"
    VALUE_FONT = "BarlowCondensed-Medium"
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False
    INK = CORAL
    TIME_INK = PINK
    ICON_INK = {}

    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        if spec is self.L["date"]:                       # the date is pink like the time
            colour = DATE_PINK
        return super().put(surf, s, spec, font, colour, tracking, distress)

    def _render_static(self, now):
        """The readouts are drawn on a clear layer first, so they can be given their halo."""
        art = self.art
        self.art = pygame.Surface(art.get_size(), pygame.SRCALPHA)
        try:
            text = super()._render_static(now)
        finally:
            self.art = art
        out = art.copy()
        out.blit(_halo(text, self.S(10), HALO, 200), (0, 0))
        out.blit(text, (0, 0))
        colon, (x, y) = self.colon                        # the blinking colon gets its own
        pad = self.S(14)
        sprite = pygame.Surface((colon.get_width() + pad * 2, colon.get_height() + pad * 2), pygame.SRCALPHA)
        sprite.blit(colon, (pad, pad))
        halo = _halo(sprite, self.S(10), HALO, 200)
        halo.blit(sprite, (0, 0))
        self.colon = (halo, (x - pad, y - pad))
        return out

    def make_effects(self):
        L = self.L
        return [
            Shimmer(self.art, L["lake"]),
            Twinkle(self.art, L["stars"], 34, _night, STAR, seed=21, avoid=L["avoid"]),
            Sparkles(L["sparkles"], STAR),
            MoonGlow(self.art, L["moons"]),
            ShootingStar(self.art, L["sky"], L["meteor_x"], STAR, L["meteor_y"]),
        ]
