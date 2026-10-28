"""Shared pieces for the retro-space poster faces (launch, astronaut, control, colony, station,
explorer): the live readout layer drawn over a prepared background, and small animations.

Each face module gives a LAYOUTS table. Landscape positions are in "poster" pixels (the mockup
scaled to 2000 px wide, as the tools/prep_*.py scripts work) and are mapped onto the 1600x720
canvas with `scale` and `offset`; portrait positions are canvas pixels (scale 1).

A readout is (x, y, cap, max_width[, anchor]); anchor defaults to "midleft". Weather rows are
dicts: kind ("temp", "humidity", "pressure", "wind"), icon (x, y, size) or None, value
(readout) and label (readout) or None. The temp row's label is the weather summary; when the
Sense HAT gives a room temperature it goes on that label, or onto the value if there is none.
"""
import math
import random

import pygame

from .. import icons, ui

ANTON = "Anton-Regular"
LABELS = {"humidity": "HUMIDITY", "pressure": "PRESSURE", "wind": "WIND"}
ICONS = {"humidity": "drop", "pressure": "gauge", "wind": "wind"}


def mapper(src, dst):
    """Point mapping for a piece of the poster ((x, y, w, h) in poster pixels) placed at `dst`
    ((x, y, w, h) canvas pixels) by a prep script's compose()."""
    kx, ky = dst[2] / src[2], dst[3] / src[3]
    return lambda x, y: (round(dst[0] + (x - src[0]) * kx), round(dst[1] + (y - src[1]) * ky))


def _star(size, colour):
    k = 4
    s = size * k
    big = pygame.Surface((s, s), pygame.SRCALPHA)
    c, t = s / 2, s * 0.045
    pygame.draw.polygon(big, colour, [(c, 0), (c + t, c - t), (s, c), (c + t, c + t),
                                      (c, s), (c - t, c + t), (0, c), (c - t, c - t)])
    return pygame.transform.smoothscale(big, (size, size))


def _glow(radius, colour):
    """Soft round light: a bright core fading out to nothing."""
    s = radius * 2 + 1
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(255 * (1 - r / radius) ** 1.8)
        pygame.draw.circle(surf, (*colour, a), (radius, radius), r)
    return surf


def _region_mask(art, rect, wanted):
    """Which pixels of `rect` satisfy wanted(r, g, b): a list of rows of booleans."""
    sub = art.subsurface(rect)
    return [[wanted(*sub.get_at((x, y))[:3]) for x in range(rect.width)] for y in range(rect.height)]


# ---- animations -------------------------------------------------------------------------
class Twinkle:
    """Faint pin-prick stars on clear patches of sky, slowly brightening and fading."""

    def __init__(self, art, sky, count, is_sky, colour, seed=1, avoid=()):
        rng, self.stars, tries = random.Random(seed), [], 0
        while len(self.stars) < count and tries < 20000:
            tries += 1
            x, y = rng.randrange(sky.left + 6, sky.right - 6), rng.randrange(sky.top + 6, sky.bottom - 6)
            if any(r.collidepoint(x, y) for r in avoid):
                continue
            patch = [art.get_at((x + dx, y + dy)) for dx in (-4, 0, 4) for dy in (-4, 0, 4)]
            if all(is_sky(p.r, p.g, p.b) for p in patch):
                self.stars.append((x, y, rng.choice((1, 1, 2)), rng.uniform(6, 14), rng.uniform(0, 1), tuple(patch[4])[:3]))
        self.colour = colour

    def draw(self, surf, t):
        for x, y, radius, period, phase, sky in self.stars:
            glow = 0.5 - 0.5 * math.cos(2 * math.pi * (t / period + phase))
            shade = tuple(int(s + (c - s) * glow * 0.85) for s, c in zip(sky, self.colour))
            pygame.draw.circle(surf, shade, (x, y), radius)


class Sparkles:
    """Four-pointed stars at (x, y, size) that swell and fade in turn."""

    def __init__(self, points, colour, seed=2):
        rng = random.Random(seed)
        self.sparkles = [(x, y, _star(max(int(size * 1.6), 4), colour), rng.uniform(8, 15), rng.uniform(0, 1))
                         for x, y, size in points]

    def draw(self, surf, t):
        for x, y, sprite, period, phase in self.sparkles:
            glow = max(math.sin(2 * math.pi * (t / period + phase)), 0) ** 2
            if glow > 0.02:
                side = max(int(sprite.get_width() * (0.55 + 0.45 * glow)), 2)
                star = pygame.transform.smoothscale(sprite, (side, side))
                star.set_alpha(int(255 * glow))
                surf.blit(star, star.get_rect(center=(x, y)))


class Meteor:
    """Every minute or few, a meteor streaks across `sky` (it is drawn only where it is inside)."""
    EVERY = (90.0, 200.0)
    LENGTH, TIME, TRAVEL = 90, 0.9, 260

    def __init__(self, art, sky, x_range, colour, y_range=None):
        self.art, self.sky, self.x_range, self.colour = art, sky, x_range, colour
        self.y_range = y_range or (sky.top + 20, sky.top + 100)
        self.meteor, self.next = None, None
        self.rng = random.Random()

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
        if k >= 1:
            self.meteor = None
            return
        hx, hy = x0 + dx * self.TRAVEL * k, y0 + dy * self.TRAVEL * k
        fade, step = math.sin(math.pi * k), 6
        for i in range(0, self.LENGTH, step):          # short segments, brightest at the head
            f = (1 - i / self.LENGTH) ** 2 * fade
            a, b = (hx - dx * i, hy - dy * i), (hx - dx * (i + step), hy - dy * (i + step))
            if self.sky.collidepoint(a) and self.sky.collidepoint(b):
                sky = self.art.get_at((int(a[0]), int(a[1])))
                c = tuple(max(0, min(255, int(sky[j] + (self.colour[j] - sky[j]) * f))) for j in range(3))
                pygame.draw.line(surf, c, a, b, 2 if i < self.LENGTH // 3 else 1)


class Flicker:
    """Brightens the pixels of `rect` that pass `wanted` by a wavering amount: flames, glowing
    screens, lit windows. The light is added to whatever is there, readouts included. `amount`
    is the strongest boost, as a fraction of `colour`."""
    LEVELS = 8

    def __init__(self, art, rect, wanted, colour, amount=0.35, speed=1.0, seed=3, steady=0.0):
        self.rect, self.speed, self.steady = rect, speed, steady
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        mask.fill((255, 255, 255, 0))
        for y, row in enumerate(_region_mask(art, rect, wanted)):
            for x, on in enumerate(row):
                if on:
                    mask.set_at((x, y), (255, 255, 255, 255))
        w, h = rect.size                                   # soften the mask's edge
        mask = pygame.transform.smoothscale(pygame.transform.smoothscale(mask, (max(w // 3, 1), max(h // 3, 1))), rect.size)
        self.frames = []
        for level in range(1, self.LEVELS + 1):
            k = amount * level / self.LEVELS
            light = pygame.Surface(rect.size, pygame.SRCALPHA)
            light.fill((*(int(c * k) for c in colour), 255))
            light.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            frame = pygame.Surface(rect.size)              # black, with the light where the mask is
            frame.blit(light, (0, 0))
            self.frames.append(frame)
        self.phase = random.Random(seed).uniform(0, 100)

    def level(self, t):
        t = t * self.speed + self.phase
        wave = 0.5 + 0.22 * math.sin(t * 7.3) + 0.16 * math.sin(t * 13.1 + 1.3) + 0.12 * math.sin(t * 23.7 + 2.1)
        return self.steady + (1 - self.steady) * min(max(wave, 0.0), 1.0)

    def draw(self, surf, t):
        level = int(self.level(t) * self.LEVELS + 0.5)
        if level:
            surf.blit(self.frames[min(level, self.LEVELS) - 1], self.rect, special_flags=pygame.BLEND_RGB_ADD)


class Ripple:
    """Lifts the pixels of `rect` that pass `wanted` (smoke, exhaust) off the picture and waves
    them: rows shift sideways (axis "x"), or columns up and down (axis "y")."""
    SUB = 3

    def __init__(self, art, rect, wanted, fill, axis="x", amplitude=2.0, speed=1.0):
        self.rect, self.axis, self.amp, self.speed = rect, axis, amplitude, speed
        sky = art.subsurface(rect).copy()
        moving = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y, row in enumerate(_region_mask(art, rect, wanted)):
            for x, on in enumerate(row):
                if on:
                    moving.set_at((x, y), sky.get_at((x, y)))
                    sky.set_at((x, y), fill(x, y) if callable(fill) else fill)
        w, h = rect.size
        wide = (w * self.SUB, h) if axis == "x" else (w, h * self.SUB)
        self.sky = pygame.transform.smoothscale(sky, wide)
        self.moving = pygame.transform.smoothscale(moving, wide)
        self.buf = self.sky.copy()

    def draw(self, surf, t):
        buf, moving, (w, h) = self.buf, self.moving, self.rect.size
        buf.blit(self.sky, (0, 0))
        t *= self.speed
        if self.axis == "x":
            for y in range(h):
                swell = math.sin(math.pi * y / h)
                shift = swell * self.amp * (math.sin(y / 11.0 - t * 2.4) + 0.5 * math.sin(y / 5.5 - t * 3.7 + 1.0))
                buf.blit(moving, (round(shift * self.SUB), y), (0, y, moving.get_width(), 1))
        else:
            for x in range(w):
                swell = math.sin(math.pi * x / w)
                shift = swell * self.amp * (math.sin(x / 11.0 - t * 2.4) + 0.5 * math.sin(x / 5.5 - t * 3.7 + 1.0))
                buf.blit(moving, (x, round(shift * self.SUB)), (x, 0, 1, moving.get_height()))
        surf.blit(pygame.transform.smoothscale(buf, self.rect.size), self.rect.topleft)


class Lamps:
    """Small lights that blink: (x, y, radius, colour, period, duty). A lamp is lit for the first
    `duty` of each `period` seconds, fading in and out a little, and the lamps are out of step."""

    def __init__(self, lamps, seed=4):
        rng = random.Random(seed)
        self.lamps = [(x, y, _glow(r, colour), period, duty, rng.uniform(0, period))
                      for x, y, r, colour, period, duty in lamps]

    def draw(self, surf, t):
        for x, y, sprite, period, duty, phase in self.lamps:
            k = ((t + phase) % period) / period
            if k < duty:
                edge = min(k, duty - k) / max(duty * 0.25, 1e-3)
                sprite.set_alpha(int(255 * min(edge, 1.0)))
                surf.blit(sprite, sprite.get_rect(center=(x, y)))


class Glint:
    """Every so often a band of light sweeps across a curved glass surface (a helmet visor):
    the pixels of `rect` inside `shape` (a polygon in canvas pixels)."""
    EVERY = (25.0, 45.0)
    TIME = 1.6

    def __init__(self, rect, shape, colour=(255, 250, 235), strength=110, width=0.16):
        self.rect, self.colour, self.strength, self.width = rect, colour, strength, width
        self.mask = pygame.Surface(rect.size)
        pygame.draw.polygon(self.mask, (255, 255, 255), [(x - rect.x, y - rect.y) for x, y in shape])
        self.buf = pygame.Surface(rect.size)
        self.next, self.start = None, None
        self.rng = random.Random()

    def draw(self, surf, t):
        if self.next is None or self.next - t > self.EVERY[1]:
            self.next = t + self.rng.uniform(5, self.EVERY[1])
        if self.start is None and t >= self.next:
            self.start, self.next = t, t + self.rng.uniform(*self.EVERY)
        if self.start is None:
            return
        k = (t - self.start) / self.TIME
        if k >= 1:
            self.start = None
            return
        w, h = self.rect.size
        buf = self.buf
        buf.fill((0, 0, 0))
        centre = -0.3 * w + k * 1.6 * w            # the band travels left to right, leaning over
        for i, (spread, power) in enumerate(((self.width, 0.45), (self.width * 0.45, 1.0))):
            half = spread * w / 2
            c = tuple(int(v * power * self.strength / 255) for v in self.colour)
            pygame.draw.polygon(buf, c, [(centre - half + h * 0.45, 0), (centre + half + h * 0.45, 0),
                                         (centre + half - h * 0.45, h), (centre - half - h * 0.45, h)])
        buf.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(buf, self.rect.topleft, special_flags=pygame.BLEND_RGB_ADD)


# ---- the face ---------------------------------------------------------------------------
class ArtworkFace:
    """Base for the poster faces. Subclasses set name, folder, LAYOUTS and the colours, and
    build their animations in make_effects()."""
    name = folder = None
    LAYOUTS = {}
    INK = (246, 236, 210)            # date, time and values
    LABEL_INK = None                 # small labels (defaults to INK)
    ICON_INK = {}                    # icon colours by row kind (defaults to INK)
    TIME_INK = None                  # the big digits (defaults to INK)
    TIME_FONT = ANTON
    DISTRESS = True

    def __init__(self, ctx):
        self.ctx = ctx
        self.L = self.LAYOUTS[ctx.orientation]
        path = ui.ASSETS / "faces" / self.folder / self.L["image"]
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        self.colon = None
        self.prepare()
        self.effects = self.make_effects()

    @classmethod
    def sizes_from(cls, layouts):
        return {name: layout["size"] for name, layout in layouts.items()}

    def P(self, x, y):
        """Layout coordinates -> canvas pixels."""
        k, (ox, oy) = self.L["scale"], self.L["offset"]
        return round(ox + x * k), round(oy + y * k)

    def S(self, v):
        return max(round(v * self.L["scale"]), 1)

    def R(self, x0, y0, x1, y1):
        """Layout box corners -> canvas rect."""
        (a, b), (c, d) = self.P(x0, y0), self.P(x1, y1)
        return pygame.Rect(a, b, c - a, d - b)

    def prepare(self):
        """Hook: draw anything permanent onto self.art (portrait panels, rules)."""

    def make_effects(self):
        return []

    def extra_static(self, surf, now, readings):
        """Hook: draw readouts of the face's own on the minute layer."""

    # ---- text layer -------------------------------------------------------------------
    def put(self, surf, s, spec, font, colour, tracking=0, distress=None):
        x, y, cap, max_w, *anchor = spec
        t = ui.text_fit(s, font, self.S(cap), colour, self.S(max_w), tracking=tracking)
        if distress is not None and self.DISTRESS:
            t = ui.distress(t, distress)
        rect = t.get_rect(**{anchor[0] if anchor else "midleft": self.P(x, y)})
        surf.blit(t, rect)
        return rect

    def _render_time(self, surf, now):
        L = self.L
        clock = now.strftime("%H:%M") if self.ctx.config["clock"]["24_hour"] else now.strftime("%I:%M").lstrip("0")
        x, y, cap, max_w, *anchor = L["time"]
        cap = self.S(cap)
        while True:
            full, ink, spans = ui.fixed_digits(clock, self.TIME_FONT, ui.size_for_cap(self.TIME_FONT, cap),
                                               self.TIME_INK or self.INK)
            if ink.width <= self.S(max_w):
                break
            cap -= 4
        if self.DISTRESS:
            full = ui.distress(full, 5)
        gx, width = spans[clock.index(":")]
        gap = pygame.Rect(gx, 0, width, full.get_height())
        cx, cy = self.P(x, y)
        anchor = anchor[0] if anchor else "midleft"
        if anchor == "midleft":
            origin = (cx - ink.x, cy - ink.centery)
        elif anchor == "midright":
            origin = (cx - ink.right, cy - ink.centery)
        else:
            origin = (cx - ink.centerx, cy - ink.centery)
        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

    def weather_values(self, w, row):
        """(value, label) for a weather row."""
        kind = row["kind"]
        room = f"{w['room_temp']:.1f}°C" if "room_temp" in w else None
        if kind == "temp":
            outside = f"{w['temp']}{w['temp_unit']}" if "temp" in w else None
            summary = w.get("summary", "NO DATA YET" if outside is None else "")
            if row.get("label"):
                label = f"{summary}  ·  ROOM {room}" if room and summary else (f"ROOM {room}" if room else summary)
                return outside or (room and f"{room} IN") or "--", label
            if room:
                return (f"{outside} OUT  {room} IN" if outside else f"{room} IN"), ""
            return outside or "--", ""
        value = {"humidity": f"{w['humidity']}%" if "humidity" in w else "--",
                 "pressure": f"{w['pressure']} hPa" if "pressure" in w else "--",
                 "wind": f"{w['wind']} {w['wind_unit']} {w['wind_dir']}" if "wind" in w else "--"}[kind]
        return value, LABELS[kind]

    def _render_static(self, now):
        L, surf = self.L, self.art.copy()
        self.put(surf, now.strftime("%a %d %b %Y").upper(), L["date"], ui.LABEL_BOLD, self.INK, tracking=L.get("date_tracking", 6), distress=3)
        self._render_time(surf, now)
        w = self.ctx.readings() or {}
        label_ink = self.LABEL_INK or self.INK
        for row in L["rows"]:
            value, label = self.weather_values(w, row)
            if row.get("icon"):
                x, y, size = row["icon"]
                name = w.get("icon", "sun") if row["kind"] == "temp" else ICONS.get(row["kind"], "thermo")
                icon = icons.icon(name, self.S(size), self.ICON_INK.get(row["kind"], self.INK))
                surf.blit(icon, icon.get_rect(center=self.P(x, y)))
            self.put(surf, value, row["value"], ui.LABEL_MED, self.INK, tracking=1, distress=4)
            if row.get("label") and label:
                self.put(surf, label, row["label"], ui.LABEL_BOLD, label_ink, tracking=2)
        for text, spec, colour, tracking in L.get("texts", ()):        # portrait labels and slogans
            self.put(surf, text, spec, ui.LABEL_BOLD, colour, tracking=tracking)
        self.extra_static(surf, now, w)
        return surf

    # ---- per frame --------------------------------------------------------------------
    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.readings_version())
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()
        if now.second % 2 == 1:
            surf.blit(*self.colon)
        for effect in self.effects:
            effect.draw(surf, t)
