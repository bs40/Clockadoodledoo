"""Cosmonaut poster face: live date and time on the red sun, weather down the right.

The background is retface4.png with its baked-in readouts painted out by
tools/prep_cosmonaut.py. On top of that the face animates:
  - she blinks every 20 s or so, and twice on every five-minute mark
  - the colon shows on odd seconds and hides on even ones
  - the poster's sparkle stars, plus some faint extra ones, twinkle slowly
  - the rocket's smoke plumes ripple
"""
import math
import random

import pygame

from .. import icons, ui

W, H = 1600, 720
PAPER = (252, 229, 188)
POSTER_RED = (233, 70, 36)
LASH = (14, 18, 28)
ANTON = "Anton-Regular"

SUN_X = 915            # readouts are centred here, on the red sun
DATE_Y, DATE_CAP = 161, 36
TIME_Y, TIME_CAP = 307, 192
TIME_MAX_W = 520

ICON_X, VALUE_X, VALUE_MAX_W = 1378, 1428, 148
ROWS_Y = (130, 237, 317, 397)

# Centres of the poster's own sparkle stars (found in background.png), with a size for each.
SPARKLES = ((618, 91, 34), (53, 97, 24), (676, 565, 36), (738, 453, 22), (1191, 78, 22))
FAINT_STARS = 28

# Eyelids, in background.png pixels. `top` is the upper edge of the eyeliner, `open` the upper
# edge of the visible eye, `shut` the lower lid; the lid's edge sweeps from `open` to `shut`.
# `skin` is where to sample the lid colour from (her eyeshadow); `lash` is the liner's thickness.
EYES = (
    {"top": ((330, 277), (337, 274), (344, 273), (354, 274), (362, 278), (369, 285), (374, 296), (377, 309)),
     "open": ((314, 311), (322, 304), (330, 297), (340, 293), (350, 292), (358, 295), (364, 301), (368, 310)),
     "shut": ((314, 311), (322, 312), (330, 312), (340, 311), (350, 310), (358, 309), (364, 309), (368, 310)),
     "skin": (300, 291), "lash": 6.0},
    {"top": ((443, 293), (448, 291), (456, 290), (463, 291), (468, 294), (472, 299)),
     "open": ((443, 296), (449, 294), (456, 293), (463, 294), (468, 297), (472, 301)),
     "shut": ((443, 298), (449, 304), (456, 308), (462, 311), (468, 312), (473, 311)),
     "skin": (300, 291), "lash": 3.5},
)
BLINK_LEVELS = 6
BLINK_EVERY = (16.0, 24.0)   # seconds between ordinary blinks
BLINK_SHUT, BLINK_HOLD, BLINK_OPEN = 0.09, 0.06, 0.14
DOUBLE_BLINK_GAP = 0.40
DOUBLE_BLINK_PERIOD = 300

PLUME = pygame.Rect(1220, 328, 98, 222)   # the smoke columns under the rocket
PLUME_SUB = 4                             # horizontal sub-pixel steps for the ripple


def _sparkle(size):
    k = 4
    s = size * k
    big = pygame.Surface((s, s), pygame.SRCALPHA)
    c, t = s / 2, s * 0.045
    pygame.draw.polygon(big, PAPER, [(c, 0), (c + t, c - t), (s, c), (c + t, c + t),
                                     (c, s), (c - t, c + t), (0, c), (c - t, c - t)])
    return pygame.transform.smoothscale(big, (size, size))


def _smooth(points, rounds=2):
    """Chaikin corner cutting, keeping the end points."""
    for _ in range(rounds):
        out = [points[0]]
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            out += [(ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25),
                    (ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75)]
        points = out + [points[-1]]
    return points


def _average_colour(surf, centre, reach=2):
    px = [surf.get_at((centre[0] + dx, centre[1] + dy))
          for dx in range(-reach, reach + 1) for dy in range(-reach, reach + 1)]
    return tuple(sum(p[c] for p in px) // len(px) for c in range(3))


def _blink_frames(art, eye):
    """Pre-render the eyelid at each stage of closing. Returns (topleft, [surface, ...])."""
    k = 4
    every = eye["top"] + eye["open"] + eye["shut"]
    box = pygame.Rect(min(p[0] for p in every) - 4, min(p[1] for p in every) - 4, 0, 0)
    box.width = max(p[0] for p in every) + 5 - box.x
    box.height = max(p[1] for p in every) + 5 - box.y
    skin = _average_colour(art, eye["skin"])
    rng = random.Random(3)

    def local(points):
        return [((x - box.x) * k, (y - box.y) * k) for x, y in points]

    frames = []
    for level in range(1, BLINK_LEVELS + 1):
        t = level / BLINK_LEVELS
        edge = _smooth([(ox + (sx - ox) * t, oy + (sy - oy) * t)
                        for (ox, oy), (sx, sy) in zip(eye["open"], eye["shut"])])
        big = pygame.Surface((box.width * k, box.height * k), pygame.SRCALPHA)
        pygame.draw.polygon(big, skin, local(_smooth(list(eye["top"])) + edge[::-1]))
        for _ in range(box.width * box.height // 5):   # print grain on the lid
            spot = (rng.randrange(big.get_width()), rng.randrange(big.get_height()))
            if big.get_at(spot).a:
                tone = rng.choice((-26, -16, 14, 22))
                pygame.draw.circle(big, tuple(min(max(c + tone, 0), 255) for c in skin), spot, rng.choice((2, 3, 4)))
        # the eyeliner rides down on the lid's edge: a band that is fattest just off-centre
        n = len(edge) - 1
        band = [(x, y - eye["lash"] * (0.35 + math.sin(math.pi * (i / n) ** 0.8) ** 0.7))
                for i, (x, y) in enumerate(edge)]
        pygame.draw.polygon(big, LASH, local(edge + band[::-1]))
        pygame.draw.lines(big, LASH, False, local(edge), k)
        frames.append(pygame.transform.smoothscale(big, box.size))
    return box.topleft, frames


def _closure(age):
    """How shut the eyes are (0..1) `age` seconds into a blink."""
    if age < 0:
        return 0.0
    if age < BLINK_SHUT:
        return age / BLINK_SHUT
    if age < BLINK_SHUT + BLINK_HOLD:
        return 1.0
    age -= BLINK_SHUT + BLINK_HOLD
    return max(1.0 - age / BLINK_OPEN, 0.0)


class CosmonautFace:
    name = "cosmonaut"
    size = (W, H)

    def __init__(self, ctx):
        self.ctx = ctx
        path = ui.ASSETS / "faces" / "cosmonaut" / "background.png"
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        self.colon = None

        rng = random.Random(7)
        self.sparkles = [(x, y, _sparkle(int(size * 1.7)), rng.uniform(9, 16), rng.uniform(0, 1))
                         for x, y, size in SPARKLES]
        self.faint = self._faint_stars(rng)

        self.eyes = [_blink_frames(self.art, eye) for eye in EYES]
        self.blinks = []          # start times of blinks in progress or queued
        self.next_blink = None
        self.last_mark = None

        self.plume_sky, self.plume_smoke = self._split_plume()
        self.plume_buf = self.plume_sky.copy()

    def _split_plume(self):
        """Lift the smoke out of the PLUME patch so it can move without dragging the sun's edge
        or the skyline with it. Returns (patch with the smoke painted out, smoke on transparent),
        both stretched PLUME_SUB times wider so rows can shift by fractions of a pixel."""
        sky = self.art.subsurface(PLUME).copy()
        smoke = pygame.Surface(PLUME.size, pygame.SRCALPHA)
        night = _average_colour(self.art, (PLUME.right - 8, PLUME.top + 40))
        for y in range(PLUME.height):
            for x in range(PLUME.width):
                c = sky.get_at((x, y))
                if c.r >= 45 and c.r < c.g * 1.8:      # cream or grey smoke; not night sky, not red
                    smoke.set_at((x, y), c)
                    sky.set_at((x, y), night)
        wide = (PLUME.width * PLUME_SUB, PLUME.height)
        return pygame.transform.smoothscale(sky, wide), pygame.transform.smoothscale(smoke, wide)

    def _faint_stars(self, rng):
        """Extra pin-prick stars on clear patches of night sky: (x, y, radius, period, phase, sky colour)."""
        stars = []
        while len(stars) < FAINT_STARS:
            x, y = rng.randrange(20, W - 20), rng.randrange(40, H - 140)
            if PLUME.inflate(30, 30).collidepoint(x, y):
                continue
            patch = [self.art.get_at((x + dx, y + dy)) for dx in (-4, 0, 4) for dy in (-4, 0, 4)]
            if all(p.r < 50 and p.g < 70 and p.b > 35 for p in patch):
                stars.append((x, y, rng.choice((1, 1, 2)), rng.uniform(7, 15), rng.uniform(0, 1),
                              tuple(patch[4])[:3]))
        return stars

    # ---- layer that only changes each minute or when the weather updates ----
    def _render_static(self, now):
        surf = self.art.copy()
        if self.ctx.config["clock"]["24_hour"]:
            clock = now.strftime("%H:%M")
        else:
            clock = now.strftime("%I:%M").lstrip("0")
        self._render_time(surf, clock)

        date = now.strftime("%a %d %b %Y").upper()
        date_surf = ui.distress(ui.text_fit(date, ANTON, DATE_CAP, PAPER, 420, tracking=3), 2)
        surf.blit(date_surf, date_surf.get_rect(center=(SUN_X, DATE_Y)))

        w = self.ctx.weather.current
        rows = (
            (icons.icon(w["icon"] if w else "sun", 80, POSTER_RED), f"{w['temp']}{w['temp_unit']}" if w else "--", 38),
            (icons.icon("drop", 58, PAPER), f"{w['humidity']}%" if w else "--", 30),
            (icons.icon("gauge", 58, PAPER), f"{w['pressure']} hPa" if w else "--", 30),
            (icons.icon("wind", 58, PAPER), f"{w['wind']} {w['wind_unit']} {w['wind_dir']}" if w else "--", 30),
        )
        for y, (icon, value, cap) in zip(ROWS_Y, rows):
            surf.blit(icon, icon.get_rect(center=(ICON_X, y)))
            value_surf = ui.text_fit(value, ui.LABEL_BOLD, cap, PAPER, VALUE_MAX_W)
            surf.blit(value_surf, value_surf.get_rect(midleft=(VALUE_X, y)))
        return surf

    def _render_time(self, surf, clock):
        """Draw the digits onto `surf`; keep the colon aside so draw() can flash it."""
        cap = TIME_CAP
        while True:
            full, ink, spans = ui.fixed_digits(clock, ANTON, ui.size_for_cap(ANTON, cap), PAPER)
            if ink.width <= TIME_MAX_W:
                break
            cap -= 4
        full = ui.distress(full, 1)
        x, width = spans[clock.index(":")]
        gap = pygame.Rect(x, 0, width, full.get_height())
        origin = (SUN_X - ink.centerx, TIME_Y - ink.centery)

        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

    # ---- per-frame animation ---------------------------------------------
    def _eye_closure(self, t):
        if self.next_blink is None or not -5 <= self.next_blink - t <= BLINK_EVERY[1] + 15:
            self.next_blink = t + random.uniform(*BLINK_EVERY)   # first frame, or the clock jumped
        mark = int(t // DOUBLE_BLINK_PERIOD)
        if self.last_mark is not None and mark != self.last_mark:
            self.blinks += [t, t + DOUBLE_BLINK_GAP]
            self.next_blink = t + random.uniform(*BLINK_EVERY)
        self.last_mark = mark
        if t >= self.next_blink:
            self.blinks.append(t)
            self.next_blink = t + random.uniform(*BLINK_EVERY)
            # don't let an ordinary blink land on top of the five-minute double
            to_mark = DOUBLE_BLINK_PERIOD - self.next_blink % DOUBLE_BLINK_PERIOD
            if to_mark < 6 or to_mark > DOUBLE_BLINK_PERIOD - 6:
                self.next_blink += 12
        length = BLINK_SHUT + BLINK_HOLD + BLINK_OPEN
        self.blinks = [start for start in self.blinks if t - start < length]
        return max((_closure(t - start) for start in self.blinks), default=0.0)

    def _draw_plume(self, surf, t):
        buf, smoke = self.plume_buf, self.plume_smoke
        buf.blit(self.plume_sky, (0, 0))
        w = smoke.get_width()
        for y in range(PLUME.height):
            swell = math.sin(math.pi * y / PLUME.height)   # still at the nozzles and at the ground
            shift = swell * (2.2 * math.sin(y / 11.0 - t * 2.4) + 1.1 * math.sin(y / 5.5 - t * 3.7 + 1.0))
            buf.blit(smoke, (round(shift * PLUME_SUB), y), (0, y, w, 1))
        surf.blit(pygame.transform.smoothscale(buf, PLUME.size), PLUME.topleft)

    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()

        if now.second % 2 == 1:
            surf.blit(*self.colon)

        self._draw_plume(surf, t)

        for x, y, radius, period, phase, sky in self.faint:
            glow = 0.5 - 0.5 * math.cos(2 * math.pi * (t / period + phase))
            shade = tuple(int(s + (c - s) * glow * 0.85) for s, c in zip(sky, PAPER))
            pygame.draw.circle(surf, shade, (x, y), radius)
        for x, y, sprite, period, phase in self.sparkles:
            glow = max(math.sin(2 * math.pi * (t / period + phase)), 0) ** 2
            if glow > 0.02:
                side = max(int(sprite.get_width() * (0.55 + 0.45 * glow)), 2)
                star = pygame.transform.smoothscale(sprite, (side, side))
                star.set_alpha(int(255 * glow))
                surf.blit(star, star.get_rect(center=(x, y)))

        closure = self._eye_closure(t)
        if closure > 0.05:
            level = min(int(closure * BLINK_LEVELS + 0.5), BLINK_LEVELS)
            if level:
                for topleft, frames in self.eyes:
                    surf.blit(frames[level - 1], topleft)
