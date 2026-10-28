"""Flower-spiral psychedelic face: date, time and weather down the left over dark, out-of-focus
starry bokeh, beside a vortex of tiny flowers in rainbow colours swirling into a bright golden
centre, with big blurred daisies in the foreground.

The backgrounds come from Psychedelic_Clock_06.png via tools/prep_spiral.py.
Animation: the spiral slowly turns, drawing its arms in towards the centre (one turn every
80 seconds; the outer arms, the big daisies and the readouts stay still, the turning part
melting into them), the golden centre glows brighter and softer, faint stars twinkle and a few
bokeh lights and starbursts glint in the dark, and the colon blinks on odd seconds. The
lettering has a soft dark halo, as the poster's own does, so it reads over the art.
"""
import math
import random

import pygame

from .. import ui
from .artwork import ArtworkFace, Sparkles, Twinkle, _glow, mapper

CREAM = (244, 221, 188)           # the big digits
PALE = (241, 216, 174)            # the date
PEACH = (244, 203, 152)           # values
ICON_INK = {"temp": (246, 176, 119), "humidity": (247, 193, 126),
            "pressure": (244, 205, 158), "wind": (242, 203, 153)}
STAR = (255, 236, 205)
GOLD = (255, 205, 130)

# Effects are placed in poster pixels (the mockup 2000 px wide) and mapped onto each canvas.
POSTER_H = 879                    # the poster's height at 2000 wide
LAND_Y = 360 - round(POSTER_H * 0.8) // 2                            # its letterbox offset
LAND = mapper((0, 0, 2000, POSTER_H), (0, LAND_Y, 1600, round(POSTER_H * 0.8)))
ART = mapper((804, 12, 697, 852), (0, 0, 720, 880))                 # portrait: same piece as prep_spiral.py
ART_FADE = (730, 880)             # portrait: where the art fades into the readout card

CENTRE = (1152, 470)              # the spiral's golden centre
TURNS = 300                       # how far out the spiral turns (its outer arms stay still) ...
STEADY = 190                      # ... turning whole within this, melting into the still art beyond
GLINTS = ((1757, 92, 20), (1702, 196, 14), (1890, 770, 16), (458, 458, 14), (1838, 60, 11))   # bokeh lights
SPARKS = ((1712, 128, 22), (1808, 214, 15), (1636, 52, 13))                                     # starbursts


def _rect(to, x0, y0, x1, y1):
    (a, b), (c, d) = to(x0, y0), to(x1, y1)
    return pygame.Rect(a, b, c - a, d - b)


def _effects(to, k):
    """Positions of the animations through the point mapping `to`, which scales by k."""
    return dict(
        centre=to(*CENTRE), turns=round(TURNS * k), steady=round(STEADY * k), k=k,
        glints=tuple(to(x, y) + (max(round(r * k), 4),) for x, y, r in GLINTS),
        sparks=tuple(to(x, y) + (max(round(r * k), 4),) for x, y, r in SPARKS),
    )


def _rows(icon_x, value_x, ys, k, cap, max_w):
    """The four weather rows (no labels), the icons sized and nudged to match the mockup's."""
    icons = {"temp": (-2, 100), "humidity": (-2, 86), "pressure": (1, 94), "wind": (-1, 100)}
    rows = []
    for kind, y in zip(("temp", "humidity", "pressure", "wind"), ys):
        dy, size = icons[kind]
        rows.append(dict(kind=kind, icon=(icon_x, y + dy * k, size * k), label=None,
                         value=(value_x, y, cap, max_w[kind] if isinstance(max_w, dict) else max_w)))
    return rows


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=0.8, offset=(0, LAND_Y),
        time=(88, 127, 158, 600), date=(106, 268, 47, 520), date_tracking=15,
        rows=_rows(128, 255, (399, 507, 619, 731), 1, 53, {"temp": 500, "humidity": 300, "pressure": 300, "wind": 300}),
        stars=(_rect(LAND, 1600, 24, 1960, 300), _rect(LAND, 1780, 620, 1960, 850)),
        avoid=(),
        source=None, fade=None,
        **_effects(LAND, 0.8),
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        time=(360, 990, 150, 640, "center"), date=(360, 1118, 40, 580, "center"), date_tracking=14,
        rows=_rows(145, 230, (1232, 1327, 1422, 1517), 0.9, 47, 450),
        stars=(pygame.Rect(16, 1160, 80, 430), pygame.Rect(610, 1270, 94, 320)), avoid=(),
        source="background.png", fade=ART_FADE,
        **_effects(ART, 720 / 697),
    ),
}


# ---- animations -------------------------------------------------------------------------
def _smooth(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def _sharpen(surf, amount=128):
    """`surf` with its fine detail (what a blur takes away) strengthened by amount/255: it makes up
    for the softening of turning and scaling it back up."""
    w, h = surf.get_size()
    blur = pygame.transform.smoothscale(pygame.transform.smoothscale(surf, (max(w // 2, 1), max(h // 2, 1))), (w, h))
    more, less = surf.copy(), blur.copy()
    more.blit(blur, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    less.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    for part in (more, less):
        part.fill((amount,) * 3, special_flags=pygame.BLEND_RGB_MULT)
    surf.blit(more, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    surf.blit(less, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    return surf


class Vortex:
    """The spiral turning: a disc of the picture `radius` px around `centre` turns clockwise
    once every `period` seconds, whole within `steady` px and melting into the still picture
    beyond (and, with `fade` (y0, y1), fading out down the canvas between those rows).

    Turning a big disc every frame is too slow for a Pi, so the disc is kept at 1/`down` of the
    canvas resolution (the art is soft: the mockup is small) and turned once at start-up to
    every `step` degrees of a quarter turn; the rest of the turn is those frames swapped round by
    whole quarter turns, which is exact and cheap. Each frame crossfades the two nearest, lays
    on the mask and scales the disc up, and only when the angle has moved on a little."""

    EVERY = 0.4                       # degrees the angle moves on before the disc is redrawn

    def __init__(self, picture, centre, radius, steady, period=80.0, step=1.5, down=2, fade=None,
                 resample=None):
        self.period, self.step = period, step
        side = radius * 2
        self.rect = pygame.Rect(0, 0, side, side)
        self.rect.center = centre
        small = max(side // down, 2)
        src = resample or self.rect
        base = pygame.transform.smoothscale(picture.subsurface(src), (small, small)).convert()
        self.frames = []
        for i in range(round(90 / step)):
            frame = base.copy()
            if i:
                turned = pygame.transform.rotozoom(base, -i * step, 1.0)
                frame.blit(turned, turned.get_rect(center=(small / 2, small / 2)))
            self.frames.append(_sharpen(frame) if down > 1 else frame)
        # The mask: opaque within `steady`, easing out to nothing at `radius`; and the fade.
        k = small / side
        mask = pygame.Surface((small, small), pygame.SRCALPHA)
        mask.fill((255, 255, 255, 0))
        for r in range(round(radius * k), 0, -1):
            a = 1 - _smooth((r / k - steady) / (radius - steady))
            pygame.draw.circle(mask, (255, 255, 255, round(255 * a)), (small / 2, small / 2), r)
        if fade:
            ramp = pygame.Surface((small, small), pygame.SRCALPHA)
            for y in range(small):
                cy = self.rect.top + (y + 0.5) / k
                ramp.fill((255, 255, 255, round(255 * (1 - _smooth((cy - fade[0]) / (fade[1] - fade[0]))))), (0, y, small, 1))
            mask.blit(ramp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.mask = mask
        self.buf = pygame.Surface((small, small)).convert()
        self.layer = pygame.Surface((small, small), pygame.SRCALPHA)
        self.big = pygame.Surface((side, side), pygame.SRCALPHA)
        self.shown = None

    def angle(self, t):
        return (t % self.period) / self.period * 360.0

    def draw(self, surf, t):
        angle = self.angle(t)
        key = round(angle / self.EVERY)
        if key != self.shown:
            self.shown = key
            quarter, rest = divmod(angle, 90.0)
            f = rest / self.step
            i, w = int(f), f - int(f)
            buf = self.buf                         # the two nearest frames, crossfaded ...
            buf.blit(self.frames[i], (0, 0))
            if w > 0.02:
                if i + 1 < len(self.frames):
                    b = self.frames[i + 1]
                else:                              # (the next is the first, a quarter on)
                    b = pygame.transform.rotate(self.frames[0], -90)
                b.set_alpha(round(255 * w))
                buf.blit(b, (0, 0))
                b.set_alpha(None)
            if quarter % 4:                        # ... turned on by whole quarters ...
                buf = pygame.transform.rotate(buf, -90 * (quarter % 4))
            self.layer.blit(buf, (0, 0))           # ... masked, and scaled up
            self.layer.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            pygame.transform.smoothscale(self.layer, self.big.get_size(), self.big)
        surf.blit(self.big, self.rect)


def _light_frames(radius, colour, levels):
    """A soft round light on black at `levels` brightnesses, for adding onto the picture."""
    sprite = _glow(radius, colour)
    frames = []
    for i in range(1, levels + 1):
        frame = pygame.Surface(sprite.get_size())
        frame.blit(sprite, (0, 0))
        v = round(255 * i / levels)
        frame.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
        frames.append(frame)
    return frames


class Core:
    """The golden centre glows brighter and softer again, slowly."""
    LEVELS = 16

    def __init__(self, centre, radius, colour, strength=0.42, period=9.0):
        self.centre, self.period = centre, period
        self.frames = _light_frames(radius, tuple(round(c * strength) for c in colour), self.LEVELS)

    def draw(self, surf, t):
        level = 0.5 - 0.5 * math.cos(2 * math.pi * t / self.period)
        i = int(level * self.LEVELS + 0.5)
        if i:
            frame = self.frames[i - 1]
            surf.blit(frame, frame.get_rect(center=self.centre), special_flags=pygame.BLEND_RGB_ADD)


class Bokeh:
    """Soft lights in the dark (x, y, radius) that now and then swell and fade, out of step."""
    LEVELS = 10

    def __init__(self, lights, colour, strength=0.5, seed=8):
        rng = random.Random(seed)
        tint = tuple(round(c * strength) for c in colour)
        self.lights = [(x, y, _light_frames(r, tint, self.LEVELS), rng.uniform(7, 13), rng.uniform(0, 1))
                       for x, y, r in lights]

    def draw(self, surf, t):
        for x, y, frames, period, phase in self.lights:
            glow = max(math.sin(2 * math.pi * (t / period + phase)), 0) ** 2
            i = int(glow * self.LEVELS + 0.5)
            if i:
                frame = frames[i - 1]
                surf.blit(frame, frame.get_rect(center=(x, y)), special_flags=pygame.BLEND_RGB_ADD)


def _halo(text, spread, strength):
    """A soft dark shadow of `text` (a surface with alpha), `spread` px beyond it each side."""
    w, h = text.get_size()
    sil = pygame.Surface((w + spread * 2, h + spread * 2), pygame.SRCALPHA)
    sil.blit(text, (spread, spread))
    sil.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MIN)          # black, same alpha
    sil = pygame.transform.gaussian_blur(sil, max(spread // 2, 1))
    sil.fill((255, 255, 255, strength), special_flags=pygame.BLEND_RGBA_MULT)
    return sil


def _night(r, g, b):
    """The dark starry background (not the bokeh, the flowers or the stars)."""
    return r < 42 and g < 46 and b < 60


class SpiralFace(ArtworkFace):
    name = "spiral"
    folder = "spiral"
    LAYOUTS = LAYOUTS
    sizes = ArtworkFace.sizes_from(LAYOUTS)
    INK = PEACH
    TIME_INK = CREAM
    ICON_INK = ICON_INK
    TIME_FONT = "Fraunces72ptSuperSoft-Black"
    DATE_FONT = ui.LABEL_MED
    VALUE_FONT = ui.LABEL_MED
    DATE_FORMAT = "%d %b %Y"
    SHORT_VALUES = True
    DISTRESS = False
    HALO = 170                    # how dark the lettering's soft shadow is (0-255)

    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        """As ArtworkFace.put, over a soft dark halo like the poster's lettering; the date is paler."""
        if spec is self.L["date"]:
            colour = PALE
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
        if L["source"]:               # portrait: turn the landscape picture, which isn't faded
            picture = pygame.image.load(str(ui.ASSETS / "faces" / self.folder / L["source"])).convert()
            r = TURNS * 0.8
            (cx, cy) = LAND(*CENTRE)
            resample = pygame.Rect(round(cx - r), round(cy - r), round(2 * r), round(2 * r))
        else:
            picture, resample = self.art, None
        effects = [Vortex(picture, L["centre"], L["turns"], L["steady"], fade=L["fade"], resample=resample),
                   Core(L["centre"], round(70 * L["k"]), GOLD)]
        for i, sky in enumerate(L["stars"]):
            effects.append(Twinkle(self.art, sky, 18, _night, STAR, seed=31 + i, avoid=L["avoid"]))
        art = self.art.get_rect() if L["fade"] is None else pygame.Rect(0, 0, L["size"][0], L["fade"][0])
        glints = [g for g in L["glints"] if art.collidepoint(g[:2])]          # those in the picture
        sparks = [s for s in L["sparks"] if art.collidepoint(s[:2])]
        if glints:
            effects.append(Bokeh(glints, GOLD))
        if sparks:
            effects.append(Sparkles(sparks, STAR, seed=9))
        return effects
