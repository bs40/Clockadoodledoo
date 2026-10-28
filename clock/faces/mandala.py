"""Mandala-meditation poster face: date, time and weather down the left beside a meditating
figure with glowing chakras, a golden mandala halo behind him, mountains and a lotus lake.

The backgrounds come from psychedelic_clock_05_mandala_meditation.png via tools/prep_mandala.py.
Animation, all on one slow breath (about 7 s): a wave of light rises up his seven chakras from
the red root to the violet crown, their reflections in the lake glowing with them; the mandala
halo brightens gently as the wave reaches the crown; a ripple spreads across the water from
where he sits once a breath; the lotus flowers glow softly, each in its own time; faint stars
twinkle in the sky by the moon; and the colon blinks on odd seconds.
"""
import math

import pygame

from .. import ui
from .artwork import ArtworkFace, Twinkle, mapper

CREAM = (242, 221, 186)           # the big digits
DATE = (250, 231, 190)
GOLD = (245, 186, 82)             # values and icons
STAR = (236, 240, 214)

PERIOD = 7.0                      # one breath, seconds

# Effects are placed in poster pixels (the mockup 2000 px wide) and mapped onto each canvas.
LAND = mapper((0, 0, 2000, 888), (0, 5, 1600, 710))                 # the letterboxed poster
ART = mapper((765, 14, 855, 826), (0, 0, 720, 696))                 # portrait: as tools/prep_mandala.py,
ART_FADE = (556, 696)                                               # the rows where it fades out,
FOOT = mapper((452, 680, 290, 178), (193, 1395, 334, 205))          # and the lotus at the foot

# The chakras from the root up: (x, y, radius, colour of their light), poster pixels.
CHAKRAS = (
    (1192, 689, 26, (255, 60, 30)),         # red, the root
    (1193, 621, 26, (255, 128, 24)),        # orange
    (1192, 545, 26, (255, 196, 40)),        # yellow
    (1192, 472, 22, (80, 232, 112)),        # green, the heart
    (1192, 405, 19, (40, 176, 255)),        # blue, the throat
    (1191, 320, 19, (92, 96, 255)),         # indigo, the brow
    (1190, 267, 17, (206, 84, 255)),        # violet, the crown
)
REFLECTIONS = ((0, 1192, 766), (1, 1192, 806), (2, 1192, 843))      # chakra, x, y in the lake
HALO = (1195, 290, 470)                                             # centre and radius
WATERLINE = (1192, 736)                                             # where he meets the water
LOTUSES = ((450, 688, 742, 868), (1726, 686, 1992, 866),            # the two big ones,
           (1630, 652, 1702, 702), (1748, 650, 1822, 700))          # two small ones on the right


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _effects(to, lotuses):
    """Positions of the animations through the point mapping `to`."""
    k = (to(1000, 0)[0] - to(0, 0)[0]) / 1000
    return dict(
        chakras=[to(x, y) + (r * k, colour) for x, y, r, colour in CHAKRAS],
        reflections=[(i,) + to(x, y) for i, x, y in REFLECTIONS],
        halo=to(*HALO[:2]) + (HALO[2] * k,),
        waterline=to(*WATERLINE), ripple=(250 * k, 430 * k),
        lotuses=lotuses,
    )


def _rows(icon_x, value_x, ys, sizes, cap, max_ws):
    return [dict(kind=kind, icon=(icon_x, y + dy, size), value=(value_x, y, cap, max_w), label=None)
            for kind, y, (dy, size), max_w in zip(("temp", "humidity", "pressure", "wind"), ys, sizes, max_ws)]


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 5),
        date=(120, 274, 44, 520), date_tracking=9, time=(96, 128, 155, 570),
        rows=_rows(131, 232, (400, 513, 627, 740), ((0, 78 * 1.25), (-2, 104), (-4, 116), (0, 108)), 55,
                   (560, 400, 400, 400)),
        stars=_rect(LAND, 1560, 20, 1975, 330),
        avoid=(_rect(LAND, 1815, 40, 1970, 210), _rect(LAND, 1700, 185, 1900, 300)),    # moon, cloud
        fade=None,
        **_effects(LAND, [_rect(LAND, *r) for r in LOTUSES]),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        date=(360, 752, 34, 600, "center"), date_tracking=10, time=(360, 870, 150, 640, "center"),
        rows=_rows(150, 242, (1020, 1120, 1220, 1320), ((0, 74 * 1.25), (-2, 96), (-4, 104), (0, 98)), 48,
                   (440, 440, 440, 440)),
        stars=None, avoid=(), fade=ART_FADE,
        **_effects(ART, [_rect(FOOT, *LOTUSES[0])]),
    ),
}


def breath(t, delay=0.0):
    """0 (breathed out) .. 1 (breathed in), `delay` breaths behind."""
    return 0.5 - 0.5 * math.cos(2 * math.pi * (t / PERIOD - delay))


def _disc(radius, colour, squash=1.0, strength=1.0):
    """A round light (black where there is none): brightest in the middle, fading to nothing."""
    r = max(int(radius), 2)
    surf = pygame.Surface((r * 2 + 1, r * 2 + 1))
    for i in range(r, 0, -1):
        k = strength * (1 - i / r) ** 1.7
        pygame.draw.circle(surf, tuple(int(c * k) for c in colour), (r, r), i)
    if squash != 1.0:
        surf = pygame.transform.smoothscale(surf, (r * 2 + 1, max(int((r * 2 + 1) * squash), 3)))
    return surf


HALO_PAD = 8


def _halo(sprite, strength=150):
    """A soft dark shadow the shape of `sprite`, HALO_PAD px bigger all round."""
    w, h = sprite.get_size()
    shadow = pygame.Surface((w + HALO_PAD * 2, h + HALO_PAD * 2), pygame.SRCALPHA)
    shadow.blit(sprite, (HALO_PAD, HALO_PAD))
    shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    sw, sh = shadow.get_size()
    shadow = pygame.transform.smoothscale(pygame.transform.smoothscale(shadow, (max(sw // 4, 1), max(sh // 4, 1))), (sw, sh))
    shadow.fill((255, 255, 255, strength), special_flags=pygame.BLEND_RGBA_MULT)
    return shadow


def _mask(art, rect, colour, threshold, blur=3):
    """White where the pixels of `rect` are within `threshold` of `colour` (per channel), softened."""
    hit = pygame.mask.from_threshold(art.subsurface(rect), colour, threshold)
    surf = pygame.Surface(rect.size)
    surf.blit(hit.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0)), (0, 0))
    w, h = rect.size
    return pygame.transform.smoothscale(pygame.transform.smoothscale(surf, (max(w // blur, 1), max(h // blur, 1))), (w, h))


def _visible(y, fade):
    """How much of the picture shows on row y: 1 above the fade (y0, y1), 0 below it."""
    if not fade:
        return 1.0
    k = min(max((y - fade[0]) / (fade[1] - fade[0]), 0.0), 1.0)
    return 1 - k * k * (3 - 2 * k)


class Glow:
    """A light (an RGB surface, black where it is dark) added over the picture at `pos`, its
    strength following level(t) from 0 to 1. The dimmed copy is only redrawn when the level
    moves a step."""
    STEPS = 40

    def __init__(self, light, pos, level):
        self.light, self.pos, self.level = light, pos, level
        self.buf, self.step = light.copy(), None

    def draw(self, surf, t):
        step = round(min(max(self.level(t), 0.0), 1.0) * self.STEPS)
        if not step:
            return
        if step != self.step:
            v = 255 * step // self.STEPS
            self.buf.blit(self.light, (0, 0))
            self.buf.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            self.step = step
        surf.blit(self.buf, self.pos, special_flags=pygame.BLEND_RGB_ADD)


def _chakra_level(i):
    """The wave of light rising up the spine: the root brightens first, the crown last."""
    return lambda t: breath(t, i * 0.075) ** 2.2


class Ripple:
    """Once a breath a ring spreads out across the lake from where he sits, slowing and fading
    as it goes. Only its near half is drawn, in front of him, and not over the lotus flowers."""
    LIFE = 12.0

    def __init__(self, art, centre, radii, lotus, colour=(120, 104, 76), squash=0.12, fade=None):
        self.centre, (self.r0, self.r1), self.colour, self.squash = centre, radii, colour, squash
        cx, cy = centre
        w, h = int(self.r1 * 2) + 8, int(self.r1 * squash) + 6
        self.rect = pygame.Rect(cx - w // 2, cy, w, h).clip(art.get_rect())
        water = pygame.Surface(self.rect.size)
        water.fill((255, 255, 255))
        water.blit(_mask(art, self.rect, *lotus), (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        if fade:                                          # where the picture fades out (portrait)
            for y in range(self.rect.height):
                v = int(255 * _visible(self.rect.y + y, fade))
                water.fill((v, v, v), (0, y, self.rect.width, 1), special_flags=pygame.BLEND_RGB_MULT)
        self.water, self.buf = water, pygame.Surface(self.rect.size)

    def draw(self, surf, t):
        buf, drawn = self.buf, False
        buf.fill((0, 0, 0))
        n = math.floor(t / PERIOD - 0.5)             # born as the light reaches the root chakra
        for born in ((n + 0.5) * PERIOD, (n - 0.5) * PERIOD):
            k = (t - born) / self.LIFE
            if not 0 <= k < 1:
                continue
            rx = self.r0 + (self.r1 - self.r0) * (1 - (1 - k) ** 2)
            ry = rx * self.squash
            fade = math.sin(math.pi * k) ** 1.5
            box = pygame.Rect(0, 0, round(rx * 2), round(ry * 2))
            box.center = (self.centre[0] - self.rect.x, self.centre[1] - self.rect.y)
            pygame.draw.ellipse(buf, tuple(int(c * fade * 0.45) for c in self.colour), box.inflate(2, 2), 4)
            pygame.draw.ellipse(buf, tuple(int(c * fade) for c in self.colour), box, 2)
            drawn = True
        if drawn:
            buf.blit(self.water, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(buf, self.rect, special_flags=pygame.BLEND_RGB_ADD)


LOTUS = ((228, 140, 132), (28, 72, 70))      # lotus pink and peach: colour, per-channel threshold


def _night(r, g, b):
    """Clear teal sky (not the moon, the cloud or the mandala's golden lines)."""
    return b > r + 30 and r < 70 and g < 130


class MandalaFace(ArtworkFace):
    name = "mandala"
    folder = "mandala"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = GOLD
    TIME_INK = CREAM
    TIME_FONT = "Jost-SemiBold"
    DATE_FONT = "Jost-SemiBold"
    VALUE_FONT = ui.LABEL_MED
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False

    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        """As ArtworkFace.put, over a soft dark halo as the mockup prints its lettering (it keeps
        the values legible over the bright clouds); the date is cream, the values gold."""
        if spec is self.L["date"]:
            colour = DATE
        x, y, cap, max_w, *anchor = spec
        t = ui.text_fit(s, font, self.S(cap), colour, self.S(max_w), tracking=tracking)
        rect = t.get_rect(**{anchor[0] if anchor else "midleft": self.P(x, y)})
        surf.blit(_halo(t), rect.move(-HALO_PAD, -HALO_PAD))
        surf.blit(t, rect)
        return rect

    def make_effects(self):
        L, art = self.L, self.art
        bounds = art.get_rect()
        effects = []

        # the mandala halo: its golden and cream pattern, lit most near his head
        cx, cy, radius = L["halo"]
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2).clip(bounds)
        light = _mask(art, rect, (210, 180, 130), (46, 76, 131))
        for x, y, r, _ in L["chakras"]:                  # not the chakras: they have their own light
            pygame.draw.circle(light, (0, 0, 0), (x - rect.x, y - rect.y), r * 1.5)
        falloff = _disc(radius, (255, 214, 150), strength=0.28)
        lit = pygame.Surface(rect.size)
        lit.blit(falloff, (cx - radius - rect.x, cy - radius - rect.y))
        light.blit(lit, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        effects.append(Glow(light, rect.topleft, lambda t: breath(t, 0.5) ** 1.5))

        # the lotus flowers, each glowing in its own time
        for i, rect in enumerate(L["lotuses"]):
            rect = rect.clip(bounds)
            if rect.width < 8 or rect.height < 8:
                continue
            light = _mask(art, rect, *LOTUS)
            light.fill((70, 40, 34), special_flags=pygame.BLEND_RGB_MULT)
            effects.append(Glow(light, rect.topleft,
                                lambda t, p=1.37 + 0.21 * i, d=0.29 * i: 0.5 - 0.5 * math.cos(2 * math.pi * (t / (PERIOD * p) - d))))

        effects.append(Ripple(art, L["waterline"], L["ripple"], LOTUS, fade=L["fade"]))

        # the chakras and their reflections
        for i, (x, y, r, colour) in enumerate(L["chakras"]):
            light = _disc(r * 2.6, colour)
            effects.append(Glow(light, light.get_rect(center=(x, y)).topleft, _chakra_level(i)))
        for i, x, y in L["reflections"]:
            r, colour = L["chakras"][i][2:]
            strength = 0.6 * _visible(y, L["fade"])
            if strength < 0.1:
                continue
            light = _disc(r * 2.2, colour, squash=0.45, strength=strength)
            effects.append(Glow(light, light.get_rect(center=(x, y)).topleft, _chakra_level(i)))

        if L["stars"]:
            effects.append(Twinkle(art, L["stars"], 22, _night, STAR, seed=23, avoid=L["avoid"]))
        return effects
