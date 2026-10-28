"""Rainbow-valley poster face: a 70s psychedelic valley, giant rainbow arcs round a setting sun
over blue mountains and a rainbow road winding through the flowers, with date, time and weather
down the left over a dark, out-of-focus foreground of flowers and night sky.

The backgrounds (and the light masks arcs.png and sunlit.png) come from
psychedelic_clock_01_rainbow_valley.png via tools/prep_rainbow.py.
Animation: the sun's glow breathes, now and then a soft light passes outward across the rainbow's
bands, the sparkle star and a couple of small ones twinkle, faint stars twinkle in the dark sky,
the odd shooting star crosses the sky top right (landscape), and the colon blinks on odd seconds.
"""
import math
import random

import pygame

from .. import ui
from .artwork import ArtworkFace, Meteor, Sparkles, Twinkle, mapper

PEACH = (242, 206, 156)           # the big digits
INK = (247, 198, 134)             # date and values
AMBER = (246, 180, 92)            # icons
STAR = (255, 240, 205)
SUNLIGHT = (255, 214, 140)
SHIMMER = (255, 236, 205)
JOST = "Jost-SemiBold"

POSTER = mapper((0, 0, 2000, 878), (0, 9, 1600, 702))       # landscape: poster -> canvas
ART = (870, 14, 840, 832)                                   # portrait: same piece as prep_rainbow.py
VALLEY = mapper(ART, (0, 0, 720, 713))

ARCS = (1285, 380, 372)           # the rainbow's bands: centre and outer radius, poster pixels
SUN = (1285, 500, 85)             # the sun's disc
SPARKLES = ((815, 212, 56), (1700, 133, 20), (1744, 97, 12))


def _rows(icon_x, value_x, specs, max_w):
    """specs: (kind, y, icon size, value cap) per row."""
    return [dict(kind=kind, icon=(icon_x, y, size), value=(value_x, y, cap, max_w), label=None)
            for kind, y, size, cap in specs]


def _poster_mask(mask):
    """A poster-sized light mask, placed on the landscape canvas like the background."""
    canvas = pygame.Surface((1600, 720))
    canvas.blit(pygame.transform.smoothscale(mask, (1600, 702)), (0, 9))
    return canvas


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 9),
        time=(62, 155, 196, 700), date=(97, 311, 46, 540), date_tracking=10,
        rows=_rows(131, 232, (("temp", 418, 98, 56), ("humidity", 531, 104, 56),
                              ("pressure", 640, 104, 56), ("wind", 752, 108, 56)), 430),
        light=_poster_mask, to_canvas=POSTER, k=0.8,
        sparkles=tuple(POSTER(x, y) + (size,) for x, y, size in SPARKLES),
        stars=pygame.Rect(POSTER(740, 12), (994, 250)),
        avoid=(pygame.Rect(POSTER(1612, 30), (60, 60)), pygame.Rect(POSTER(1798, 25), (110, 110)),
               pygame.Rect(POSTER(1720, 165), (70, 70))),                  # the planets
        meteor=(pygame.Rect(POSTER(1560, 14), (340, 230)), (1300, 1560), (20, 90)),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        time=(360, 865, 158, 640, "center"), date=(360, 990, 34, 560, "center"), date_tracking=13,
        rows=_rows(205, 275, (("temp", 1112, 80, 46), ("humidity", 1217, 84, 46),
                              ("pressure", 1322, 84, 46), ("wind", 1427, 88, 46)), 400),
        light=lambda mask: pygame.transform.smoothscale(mask.subsurface(ART), (720, 713)),
        to_canvas=VALLEY, k=720 / ART[2],
        sparkles=(VALLEY(1700, 133) + (16,),),
        stars=pygame.Rect(560, 0, 160, 300),
        avoid=(pygame.Rect(600, 10, 80, 80),),
        meteor=None,                      # too little open sky up there for a shooting star
    ),
}


def _night(r, g, b):
    """Clear dark-blue night sky (not the planets, bands or clouds)."""
    return b > r + 6 and r < 70 and g < 100 and b < 130


def _halo(surf, grow, alpha=210):
    """A soft dark outline for lettering, like the poster's own: `surf`'s shape, dilated by
    `grow` px and blurred. Returns (halo, pad)."""
    pad = grow * 2
    w, h = surf.get_width() + pad * 2, surf.get_height() + pad * 2
    shape = surf.copy()
    shape.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MIN)       # black, same alpha
    halo = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in range(-grow, grow + 1):
        for dy in range(-grow, grow + 1):
            if dx * dx + dy * dy <= grow * grow:
                halo.blit(shape, (pad + dx, pad + dy))
    small = pygame.transform.smoothscale(halo, (max(w // 3, 1), max(h // 3, 1)))
    halo = pygame.transform.smoothscale(small, (w, h))
    halo.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    return halo, pad


class SunGlow:
    """The sun's glow breathing: warm light round the disc, on the sky and bands above the
    mountains (`mask`), slowly swelling and fading."""
    LEVELS = 12

    def __init__(self, mask, centre, radius, colour, amount=0.32, period=9.0):
        self.period = period
        cx, cy = centre
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2).clip(mask.get_rect())
        glow = pygame.Surface(rect.size)
        for r in range(radius, 0, -2):                     # bright core fading out to nothing
            k = (1 - r / radius) ** 1.6
            pygame.draw.circle(glow, tuple(int(c * k) for c in colour), (cx - rect.x, cy - rect.y), r)
        glow.blit(mask, (0, 0), rect, special_flags=pygame.BLEND_RGB_MULT)
        self.rect, self.frames = rect, []
        for level in range(1, self.LEVELS + 1):
            frame = glow.copy()
            v = int(255 * amount * level / self.LEVELS)
            frame.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            self.frames.append(frame)

    def draw(self, surf, t):
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * t / self.period)
        level = int(breath * self.LEVELS + 0.5)
        if level:
            surf.blit(self.frames[level - 1], self.rect, special_flags=pygame.BLEND_RGB_ADD)


class Shimmer:
    """Every so often a soft band of light passes outward across the rainbow's bands: a ring
    widening from the centre of the arcs, lit only where `mask` is."""
    EVERY = (9.0, 16.0)
    TIME = 4.5
    STEPS = 6

    def __init__(self, mask, centre, radius, colour, strength=64, width=34):
        self.centre, self.r0, self.r1 = centre, radius * 0.22, radius * 1.05
        self.colour, self.strength, self.width = colour, strength, width
        cx, cy = centre
        self.rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2).clip(mask.get_rect())
        self.mask = mask.subsurface(self.rect).copy()
        self.buf = pygame.Surface(self.rect.size)
        self.next, self.start = None, None
        self.rng = random.Random()

    def draw(self, surf, t):
        if self.next is None or not -5 <= self.next - t <= self.EVERY[1] + 5:
            self.next = t + self.rng.uniform(2, self.EVERY[1])     # first frame, or the clock jumped
        if self.start is None and t >= self.next:
            self.start, self.next = t, t + self.TIME + self.rng.uniform(*self.EVERY)
        if self.start is None:
            return
        k = (t - self.start) / self.TIME
        if not 0 <= k < 1:
            self.start = None
            return
        radius = self.r0 + (self.r1 - self.r0) * (1 - (1 - k) ** 1.6)      # slowing as it widens
        power = math.sin(math.pi * k) ** 0.7
        half = self.width / 2
        cx, cy = self.centre[0] - self.rect.x, self.centre[1] - self.rect.y
        box = pygame.Rect(0, 0, 0, 0).inflate(round(radius + half + 2) * 2, round(radius + half + 2) * 2)
        box.center = (cx, cy)
        box = box.clip(self.buf.get_rect())
        if not box.width or not box.height:
            return
        buf = self.buf
        buf.set_clip(box)
        buf.fill((0, 0, 0))
        for i in range(1, self.STEPS + 1):                 # nested rings: brightest mid-band
            h = half * (1 - (i - 1) / self.STEPS)
            v = power * self.strength * i / self.STEPS / 255
            pygame.draw.circle(buf, tuple(int(c * v) for c in self.colour), (cx, cy),
                               round(radius + h), max(round(h * 2), 1))
        buf.blit(self.mask, box, box, special_flags=pygame.BLEND_RGB_MULT)
        buf.set_clip(None)
        surf.blit(buf, (self.rect.x + box.x, self.rect.y + box.y), box, special_flags=pygame.BLEND_RGB_ADD)


class NightMeteor(Meteor):
    """Meteor that shows only against the night sky, passing behind the planets and arcs."""

    def draw(self, surf, t):
        if self.next is None or self.next - t > self.EVERY[1]:
            self.next = t + self.rng.uniform(*self.EVERY)
        if self.meteor is None and t >= self.next:
            angle = math.radians(self.rng.uniform(15, 35))
            self.meteor = (t, self.rng.uniform(*self.x_range), self.rng.uniform(*self.y_range),
                           math.cos(angle) * (1 if self.rng.random() < 0.5 else -1), math.sin(angle))
            self.next = t + self.rng.uniform(*self.EVERY)
        if self.meteor is None:
            return
        start, x0, y0, dx, dy = self.meteor
        k = (t - start) / self.TIME
        if not 0 <= k < 1:
            self.meteor = None
            return
        hx, hy = x0 + dx * self.TRAVEL * k, y0 + dy * self.TRAVEL * k
        fade, step = math.sin(math.pi * k), 6
        for i in range(0, self.LENGTH, step):          # short segments, brightest at the head
            f = (1 - i / self.LENGTH) ** 2 * fade
            a, b = (hx - dx * i, hy - dy * i), (hx - dx * (i + step), hy - dy * (i + step))
            if self.sky.collidepoint(a) and self.sky.collidepoint(b):
                sky = self.art.get_at((int(a[0]), int(a[1])))
                if _night(*sky[:3]) and _night(*self.art.get_at((int(b[0]), int(b[1])))[:3]):
                    c = tuple(max(0, min(255, int(sky[j] + (self.colour[j] - sky[j]) * f))) for j in range(3))
                    pygame.draw.line(surf, c, a, b, 2 if i < self.LENGTH // 3 else 1)


class RainbowFace(ArtworkFace):
    name = "rainbow"
    folder = "rainbow"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = INK
    TIME_INK = PEACH
    ICON_INK = {"temp": AMBER, "humidity": AMBER, "pressure": AMBER, "wind": AMBER}
    TIME_FONT = "Fraunces72ptSuperSoft-Black"
    DATE_FONT = JOST
    VALUE_FONT = ui.LABEL_MED
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False

    # ---- lettering with a soft dark outline, as printed on the poster ---------------------
    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        x, y, cap, max_w, *anchor = spec
        t = ui.text_fit(s, font, self.S(cap), colour, self.S(max_w), tracking=tracking)
        rect = t.get_rect(**{anchor[0] if anchor else "midleft": self.P(x, y)})
        halo, pad = _halo(t, 2, 170)
        surf.blit(halo, (rect.x - pad, rect.y - pad))
        surf.blit(t, rect)
        return rect

    def _render_time(self, surf, now):
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        super()._render_time(layer, now)
        box = layer.get_bounding_rect()
        halo, pad = _halo(layer.subsurface(box), 3)
        surf.blit(halo, (box.x - pad, box.y - pad))
        surf.blit(layer, box, box)
        colon, (x, y) = self.colon                        # the colon gets its own outline
        halo, pad = _halo(colon, 3)
        halo.blit(colon, (pad, pad))
        self.colon = (halo, (x - pad, y - pad))

    def make_effects(self):
        L = self.L
        to_canvas, k = L["to_canvas"], L["k"]
        arcs = L["light"](pygame.image.load(str(ui.ASSETS / "faces" / self.folder / "arcs.png")).convert())
        sunlit = L["light"](pygame.image.load(str(ui.ASSETS / "faces" / self.folder / "sunlit.png")).convert())
        effects = [
            SunGlow(sunlit, to_canvas(*SUN[:2]), round(SUN[2] * 2.6 * k), SUNLIGHT),
            Shimmer(arcs, to_canvas(*ARCS[:2]), round(ARCS[2] * k), SHIMMER),
            Twinkle(self.art, L["stars"], 30, _night, STAR, seed=21, avoid=L["avoid"]),
            Sparkles(L["sparkles"], STAR),
        ]
        if L["meteor"]:
            sky, x_range, y_range = L["meteor"]
            effects.append(NightMeteor(self.art, sky, x_range, STAR, y_range))
        return effects
