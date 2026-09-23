"""Saturn-scape poster face: day, date, time and weather in the right-hand column.

The background is retface3.png with its baked-in readouts painted out by tools/prep_saturn.py.
Animation: the poster's sparkle stars and some faint extra ones twinkle, the colon blinks on
odd seconds, and every so often a meteor streaks across the sky.
"""
import math
import random

import pygame

from .. import ui

W, H = 1600, 720
K = 1600 / 1942
Y0 = (H - 809 * K) / 2

PAPER = (246, 232, 204)
ANTON = "Anton-Regular"

COL_X = 1355                       # left edge of the text column, in retface3 pixels
DAY_Y, DAY_CAP = 88, 44
DATE_Y, DATE_CAP = 152, 44
TIME_CX, TIME_Y, TIME_CAP, TIME_MAX_W = 1622, 288, 158, 470
VALUE_X, VALUE_CAP = 1640, 30
VALUE_YS = (428, 490, 551, 612)    # temp, humidity, pressure, wind

# Poster sparkle stars in background.png pixels, filled in from tools/findstars output.
SPARKLES = ((624, 177, 39), (664, 341, 20), (993, 84, 26), (1063, 406, 18), (717, 126, 30))
FAINT_STARS = 40
SKY = pygame.Rect(0, 30, 1100, 330)          # where faint stars may be placed (above the rings)
METEOR_EVERY = (90.0, 200.0)                 # seconds between meteors
METEOR_LEN, METEOR_TIME = 90, 0.9


def P(x, y):
    return round(x * K), round(Y0 + y * K)


def _sparkle(size):
    k = 4
    s = size * k
    big = pygame.Surface((s, s), pygame.SRCALPHA)
    c, t = s / 2, s * 0.045
    pygame.draw.polygon(big, PAPER, [(c, 0), (c + t, c - t), (s, c), (c + t, c + t),
                                     (c, s), (c - t, c + t), (0, c), (c - t, c - t)])
    return pygame.transform.smoothscale(big, (size, size))


class SaturnFace:
    name = "saturn"
    size = (W, H)

    def __init__(self, ctx):
        self.ctx = ctx
        path = ui.ASSETS / "faces" / "saturn" / "background.png"
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        self.colon = None
        rng = random.Random(11)
        self.sparkles = [(x, y, _sparkle(int(size * 1.6)), rng.uniform(8, 15), rng.uniform(0, 1))
                         for x, y, size in SPARKLES]
        self.faint = self._faint_stars(rng)
        self.meteor = None          # (start_time, x0, y0, dx, dy)
        self.next_meteor = None
        self.rng = random.Random()

    def _faint_stars(self, rng):
        stars = []
        while len(stars) < FAINT_STARS:
            x, y = rng.randrange(SKY.left + 10, SKY.right - 10), rng.randrange(SKY.top + 10, SKY.bottom - 10)
            patch = [self.art.get_at((x + dx, y + dy)) for dx in (-4, 0, 4) for dy in (-4, 0, 4)]
            if all(p.r < 70 and p.g < 90 and p.b < 100 for p in patch):
                stars.append((x, y, rng.choice((1, 1, 2)), rng.uniform(6, 14), rng.uniform(0, 1), tuple(patch[4])[:3]))
        return stars

    # ---- text layer -------------------------------------------------------------------
    def _render_static(self, now):
        surf = self.art.copy()
        day = ui.distress(ui.text_fit(now.strftime("%A").upper(), ui.LABEL_BOLD, round(DAY_CAP * K), PAPER, 440, tracking=2), 3)
        surf.blit(day, day.get_rect(midleft=P(COL_X, DAY_Y)))
        date = ui.distress(ui.text_fit(now.strftime("%d %B %Y").upper(), ui.LABEL_BOLD, round(DATE_CAP * K), PAPER, 450, tracking=2), 4)
        surf.blit(date, date.get_rect(midleft=P(COL_X, DATE_Y)))

        clock = now.strftime("%H:%M") if self.ctx.config["clock"]["24_hour"] else now.strftime("%I:%M").lstrip("0")
        cap = round(TIME_CAP * K)
        while True:
            full, ink, spans = ui.fixed_digits(clock, ANTON, ui.size_for_cap(ANTON, cap), PAPER)
            if ink.width <= TIME_MAX_W * K:
                break
            cap -= 4
        full = ui.distress(full, 5)
        x, width = spans[clock.index(":")]
        gap = pygame.Rect(x, 0, width, full.get_height())
        cx, cy = P(TIME_CX, TIME_Y)
        origin = (cx - ink.centerx, cy - ink.centery)
        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

        w = self.ctx.weather.current
        values = (f"{w['temp']}{w['temp_unit']}", f"{w['humidity']}%", f"{w['pressure']} hPa",
                  f"{w['wind']} {w['wind_unit']} {w['wind_dir']}") if w else ("--",) * 4
        for value, y in zip(values, VALUE_YS):
            t = ui.text_fit(value, ui.LABEL_MED, round(VALUE_CAP * K), PAPER, 210, tracking=1)
            surf.blit(t, t.get_rect(midleft=P(VALUE_X, y)))
        return surf

    # ---- per frame --------------------------------------------------------------------
    def _draw_meteor(self, surf, t):
        if self.next_meteor is None or self.next_meteor - t > METEOR_EVERY[1]:
            self.next_meteor = t + self.rng.uniform(*METEOR_EVERY)
        if self.meteor is None and t >= self.next_meteor:
            angle = math.radians(self.rng.uniform(15, 35))
            self.meteor = (t, self.rng.uniform(350, 950), self.rng.uniform(50, 130),
                           math.cos(angle) * (1 if self.rng.random() < 0.5 else -1), math.sin(angle))
            self.next_meteor = t + self.rng.uniform(*METEOR_EVERY)
        if self.meteor is None:
            return
        start, x0, y0, dx, dy = self.meteor
        k = (t - start) / METEOR_TIME
        if k >= 1:
            self.meteor = None
            return
        travel = 260
        hx, hy = x0 + dx * travel * k, y0 + dy * travel * k
        fade = math.sin(math.pi * k)
        step = 6
        for i in range(0, METEOR_LEN, step):          # short segments, brightest at the head
            f = (1 - i / METEOR_LEN) ** 2 * fade
            a, b = (hx - dx * i, hy - dy * i), (hx - dx * (i + step), hy - dy * (i + step))
            if SKY.collidepoint(a) and SKY.collidepoint(b):
                sky = self.art.get_at((int(a[0]), int(a[1])))
                c = tuple(max(0, min(255, int(sky[j] + (PAPER[j] - sky[j]) * f))) for j in range(3))
                pygame.draw.line(surf, c, a, b, 2 if i < METEOR_LEN // 3 else 1)

    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()

        if now.second % 2 == 1:
            surf.blit(*self.colon)

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
        self._draw_meteor(surf, t)
