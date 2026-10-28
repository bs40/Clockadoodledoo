"""Flower-tunnel poster face: date, time and weather down the left over dark blurred bokeh,
beside a tunnel of orange, pink and blue flowers that recedes to a glowing golden light, its
reflection shimmering on the water below.

The backgrounds come from psychedelic_clock_03_flower_tunnel.png via tools/prep_tunnel.py.
Animation: the light at the end of the tunnel slowly breathes, its golden reflection wavers on
the water, specks of light drift out of the tunnel towards the viewer, now and then a soft ring
of light travels out through the rings of flowers, a few glints twinkle, and the colon blinks
on odd seconds.
"""
import math
import random

import pygame

from .. import ui
from .artwork import ArtworkFace, Sparkles, _glow, mapper

CREAM = (226, 219, 188)           # the big digits
PALE = (246, 244, 220)            # the date
CORAL = (244, 140, 116)           # values and icons
GOLD = (255, 190, 110)            # the light and its pulse
SPECK = (255, 226, 170)           # drifting specks and glints

# Effects are placed in poster pixels (the mockup 2000 px wide) and mapped onto each canvas.
LAND = mapper((0, 0, 2000, 846), (0, 22, 1600, 677))               # the letterboxed poster
TUNNEL = mapper((967, 10, 731, 812), (0, 0, 720, 800))             # portrait: same piece as prep_tunnel.py

LIGHT = (1330, 488)               # the light at the end of the tunnel
HORIZON = 556                     # where the water meets the tunnel's far end
WATER = (1190, 556, 1480, 828)    # the golden path on the water and the reflections beside it
GLINTS = ((1543, 232, 24), (1095, 258, 18), (1640, 400, 16), (1213, 612, 13))   # gold twigs, a lily


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _effects(to, k):
    """Positions of the animations through the point mapping `to`, which scales by k."""
    return dict(
        light=to(*LIGHT), horizon=to(0, HORIZON)[1], k=k,
        water=_rect(to, *WATER),
        glints=tuple(to(x, y) + (round(size * k),) for x, y, size in GLINTS),
    )


def _rows(icon_x, value_x, ys, k, cap, max_w):
    """The four weather rows (no labels). The icons are sized and nudged to match the mockup's:
    the sun's disc and rays, the drop, the gauge and the wind's three strokes, scaled by k."""
    icons = {"temp": (0, 108), "humidity": (3, 100), "pressure": (-5, 108), "wind": (-6, 115)}
    rows = []
    for kind, y in zip(("temp", "humidity", "pressure", "wind"), ys):
        dy, size = icons[kind]
        rows.append(dict(kind=kind, icon=(icon_x, y + dy * k, size * k), label=None,
                         value=(value_x, y, cap, max_w[kind] if isinstance(max_w, dict) else max_w)))
    return rows


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, 22),
        time=(63, 148, 164, 700), date=(100, 302, 46, 520), date_tracking=17,
        rows=_rows(131, 232, (417, 527, 637, 745), 1, 51, {"temp": 350, "humidity": 300, "pressure": 300, "wind": 300}),
        **_effects(LAND, 0.8),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        time=(360, 905, 150, 650, "center"), date=(360, 1040, 40, 560, "center"), date_tracking=16,
        rows=_rows(200, 280, (1160, 1268, 1376, 1484), 0.9, 48, 390),
        **_effects(TUNNEL, 720 / 731),
    ),
}


# ---- animations -------------------------------------------------------------------------
def _light_frames(radius, colour, levels, grow=0.0, core=0.0):
    """A soft round light drawn on black at `levels` brightnesses, for adding onto the picture;
    with `grow`, the dimmer ones are also that much smaller; with `core`, it has a bright centre
    that big (a fraction of the radius)."""
    frames = []
    for i in range(1, levels + 1):
        k = i / levels
        r = max(round(radius * (1 - grow * (1 - k))), 1)
        frame = pygame.Surface((r * 2 + 1, r * 2 + 1))
        frame.blit(_glow(r, colour), (0, 0))
        if core:
            frame.blit(_glow(max(round(r * core), 1), colour), (r - max(round(r * core), 1),) * 2,
                       special_flags=pygame.BLEND_RGB_ADD)
        v = round(255 * k)
        frame.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
        frames.append(frame)
    return frames


class Breath:
    """The light at the end of the tunnel slowly brightens and swells, then dims again."""
    LEVELS = 16

    def __init__(self, centre, radius, colour, strength=0.6, period=7.5):
        self.centre, self.period = centre, period
        self.frames = _light_frames(radius, tuple(round(c * strength) for c in colour), self.LEVELS, grow=0.3)

    def draw(self, surf, t):
        level = 0.5 - 0.5 * math.cos(2 * math.pi * t / self.period)
        i = int(level * self.LEVELS + 0.5)
        if i:
            frame = self.frames[i - 1]
            surf.blit(frame, frame.get_rect(center=self.centre), special_flags=pygame.BLEND_RGB_ADD)


class Shimmer:
    """The reflection on the water wavers: the rows of `rect` slide gently from side to side,
    the waves crowding together towards the far end and growing towards the viewer. The sliding
    fades out towards the rect's sides, so it stays on the golden path."""

    def __init__(self, art, rect, amplitude=2.6, waves=6.0, speed=1.0):
        self.rect, self.amp, self.waves, self.speed = rect, amplitude, waves, speed
        self.base = art.subsurface(rect).copy()
        w, h = rect.size
        self.moving = pygame.Surface((w, h), pygame.SRCALPHA)
        self.moving.blit(self.base, (0, 0))
        fade = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):                                  # opaque in the middle, clear at the sides
            k = min(x / (w * 0.35), (w - 1 - x) / (w * 0.35), 1.0)
            fade.fill((255, 255, 255, round(255 * k * k * (3 - 2 * k))), (x, 0, 1, h))
        self.moving.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.depth = [math.sqrt((y + 1) / h) for y in range(h)]
        self.buf = self.base.copy()

    def draw(self, surf, t):
        buf, moving, w = self.buf, self.moving, self.rect.width
        buf.blit(self.base, (0, 0))
        t *= self.speed
        amp, waves = self.amp, self.waves * 2 * math.pi
        for y, d in enumerate(self.depth):
            phase = waves * d
            shift = round(amp * (0.3 + 0.7 * d * d) * (math.sin(phase - t * 1.6) + 0.45 * math.sin(phase * 2.3 + t * 1.1 + 1.0)))
            if shift:
                buf.blit(moving, (shift, y), (0, y, w, 1))
        surf.blit(buf, self.rect.topleft)


class Motes:
    """Specks of golden light drift out of the tunnel towards the viewer, swelling and speeding
    up as they come, and fade away. Each takes a new direction every time round."""
    LEVELS = 8

    def __init__(self, centre, reach, count, colour, k=1.0, seed=6):
        rng = random.Random(seed)
        self.centre, self.reach = centre, reach
        self.sizes = [_light_frames(max(round(r * k), 2), colour, self.LEVELS, core=0.4) for r in (5, 7, 9, 11, 13)]
        self.motes = [[rng.uniform(7.0, 12.0), rng.uniform(0, 1), seed * 1000 + i, None, 0.0] for i in range(count)]

    def draw(self, surf, t):
        cx, cy = self.centre
        for mote in self.motes:
            period, phase, ident, lap, angle = mote
            u, n = math.modf(t / period + phase)
            if n != lap:                                     # a new trip: a new direction
                mote[3], mote[4] = n, random.Random(ident * 7919 + int(n)).uniform(0, 2 * math.pi)
                angle = mote[4]
            r = self.reach * (0.06 + 0.94 * u * u)
            glow = math.sin(math.pi * u) ** 1.5
            level = int(glow * self.LEVELS + 0.5)
            if level:
                frames = self.sizes[min(int(u * len(self.sizes)), len(self.sizes) - 1)]
                frame = frames[level - 1]
                surf.blit(frame, frame.get_rect(center=(cx + math.cos(angle) * r, cy + math.sin(angle) * r * 0.9)),
                          special_flags=pygame.BLEND_RGB_ADD)


class Pulse:
    """Every half a minute or so a soft ring of light travels out from the tunnel's light
    through the rings of flowers, faster as it nears, fading as it goes. It is an arch: the
    part that would cross the water is left out."""
    EVERY = (25.0, 45.0)
    TIME = 4.5
    LEVELS = 8

    def __init__(self, centre, reach, horizon, colour, k=1.0, strength=0.55):
        self.centre, self.reach, self.horizon = centre, reach, horizon
        self.spacing = 9 * k
        self.frames = _light_frames(max(round(11 * k), 3), tuple(round(c * strength) for c in colour), self.LEVELS)
        self.next, self.start = None, None
        self.rng = random.Random()

    def draw(self, surf, t):
        if self.next is None or not -5 <= self.next - t <= self.EVERY[1] + 5:
            self.next = t + self.rng.uniform(6, self.EVERY[1])       # first frame, or the clock jumped
        if self.start is None and t >= self.next:
            self.start, self.next = t, t + self.rng.uniform(*self.EVERY)
        if self.start is None:
            return
        u = (t - self.start) / self.TIME
        if not 0 <= u < 1:
            self.start = None
            return
        r = self.reach * (0.08 + 0.92 * u ** 1.6)
        level = min(int(math.sin(math.pi * u) * (1 - 0.5 * u) * self.LEVELS + 0.5), self.LEVELS)
        if not level:
            return
        frame = self.frames[level - 1]
        half = frame.get_width() // 2
        cx, cy = self.centre
        n = max(int(2 * math.pi * r / self.spacing), 8)
        for j in range(n):
            a = 2 * math.pi * j / n
            y = cy + math.sin(a) * r * 0.92
            if y < self.horizon:
                surf.blit(frame, (cx + math.cos(a) * r - half, y - half), special_flags=pygame.BLEND_RGB_ADD)


class TunnelFace(ArtworkFace):
    name = "tunnel"
    folder = "tunnel"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    TIME_FONT = "Fraunces72ptSuperSoft-Black"
    DATE_FONT = ui.LABEL_MED
    VALUE_FONT = ui.LABEL_MED
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False
    INK = CORAL                   # values and icons
    TIME_INK = CREAM

    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        if spec is self.L["date"]:            # the date is pale cream, not coral
            colour = PALE
        return super().put(surf, s, spec, font, colour, tracking, distress)

    def make_effects(self):
        L, k = self.L, self.L["k"]
        return [
            Shimmer(self.art, L["water"], amplitude=2.6 * k / 0.8),
            Breath(L["light"], round(150 * k), GOLD),
            Pulse(L["light"], 330 * k, L["horizon"], GOLD, k),
            Motes(L["light"], 320 * k, 7, SPECK, k),
            Sparkles(L["glints"], SPECK),
        ]
