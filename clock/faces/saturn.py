"""Saturn-scape poster face: day, date, time and weather beside (landscape) or below (portrait)
the scenery.

The backgrounds come from retface3.png via tools/prep_saturn.py. Animation: the poster's sparkle
stars and some faint extra ones twinkle, the colon blinks on odd seconds, and every so often a
meteor streaks across the sky.
"""
import math
import random

import pygame

from .. import ui

PAPER = (246, 232, 204)
AMBER = (232, 160, 60)
ANTON = "Anton-Regular"

# Landscape positions are in retface3.png pixels (scaled by K into the 1600x720 background);
# portrait positions are canvas pixels. Caps and widths are given in layout units too.
K = 1600 / 1942
Y0 = (720 - 809 * K) / 2

LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=K, offset=(0, Y0),
        day=(1355, 88, 44, 440), date=(1355, 152, 44, 450), time=(1622, 288, 158, 470),
        values=[(1640, y, 30, 210) for y in (428, 490, 551, 612)], labels=None, rule=None, slogan=None,
        sparkles=((624, 177, 39), (664, 341, 20), (993, 84, 26), (1063, 406, 18), (717, 126, 30)),
        sky=pygame.Rect(0, 30, 1100, 330), meteor_x=(350, 950), faint=40,
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0),
        day=(70, 880, 40, 600), date=(70, 942, 40, 600), time=(360, 1080, 150, 620),
        values=[(330, y, 30, 330) for y in (1200, 1258, 1316, 1374)],
        labels=[(70, y, label) for y, label in zip((1200, 1258, 1316, 1374), ("TEMP", "HUMIDITY", "PRESSURE", "WIND"))],
        rule=((44, 850), (44, 1400)), slogan=(360, 1500, "SOMEWHERE OUT THERE"),
        sparkles=((517, 182, 39), (566, 381, 20), (630, 120, 30)),
        sky=pygame.Rect(0, 20, 720, 310), meteor_x=(120, 620), faint=48,
    ),
}


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
    sizes = {name: layout["size"] for name, layout in LAYOUTS.items()}
    METEOR_EVERY = (90.0, 200.0)      # seconds between meteors
    METEOR_LEN, METEOR_TIME = 90, 0.9

    def __init__(self, ctx):
        self.ctx = ctx
        self.L = LAYOUTS[ctx.orientation]
        path = ui.ASSETS / "faces" / "saturn" / self.L["image"]
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        self.colon = None
        rng = random.Random(11)
        self.sparkles = [(x, y, _sparkle(int(size * 1.6)), rng.uniform(8, 15), rng.uniform(0, 1))
                         for x, y, size in self.L["sparkles"]]
        self.faint = self._faint_stars(rng)
        self.meteor = None          # (start_time, x0, y0, dx, dy)
        self.next_meteor = None
        self.rng = random.Random()

    def P(self, x, y):
        """Layout coordinates -> canvas pixels."""
        k, (ox, oy) = self.L["scale"], self.L["offset"]
        return round(ox + x * k), round(oy + y * k)

    def S(self, v):
        return round(v * self.L["scale"])

    def _faint_stars(self, rng):
        stars, sky, tries = [], self.L["sky"], 0
        while len(stars) < self.L["faint"] and tries < 20000:
            tries += 1
            x, y = rng.randrange(sky.left + 10, sky.right - 10), rng.randrange(sky.top + 10, sky.bottom - 10)
            patch = [self.art.get_at((x + dx, y + dy)) for dx in (-4, 0, 4) for dy in (-4, 0, 4)]
            if all(p.r < 70 and p.g < 90 and p.b < 100 for p in patch):
                stars.append((x, y, rng.choice((1, 1, 2)), rng.uniform(6, 14), rng.uniform(0, 1), tuple(patch[4])[:3]))
        return stars

    # ---- text layer -------------------------------------------------------------------
    def _render_static(self, now):
        L, surf = self.L, self.art.copy()
        x, y, cap, max_w = L["day"]
        day = ui.distress(ui.text_fit(now.strftime("%A").upper(), ui.LABEL_BOLD, self.S(cap), PAPER, self.S(max_w), tracking=2), 3)
        surf.blit(day, day.get_rect(midleft=self.P(x, y)))
        x, y, cap, max_w = L["date"]
        date = ui.distress(ui.text_fit(now.strftime("%d %B %Y").upper(), ui.LABEL_BOLD, self.S(cap), PAPER, self.S(max_w), tracking=2), 4)
        surf.blit(date, date.get_rect(midleft=self.P(x, y)))

        clock = now.strftime("%H:%M") if self.ctx.config["clock"]["24_hour"] else now.strftime("%I:%M").lstrip("0")
        cx, cy, cap, max_w = L["time"]
        cap = self.S(cap)
        while True:
            full, ink, spans = ui.fixed_digits(clock, ANTON, ui.size_for_cap(ANTON, cap), PAPER)
            if ink.width <= self.S(max_w):
                break
            cap -= 4
        full = ui.distress(full, 5)
        gx, width = spans[clock.index(":")]
        gap = pygame.Rect(gx, 0, width, full.get_height())
        cx, cy = self.P(cx, cy)
        origin = (cx - ink.centerx, cy - ink.centery)
        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

        w = self.ctx.weather.current
        values = (f"{w['temp']}{w['temp_unit']}", f"{w['humidity']}%", f"{w['pressure']} hPa",
                  f"{w['wind']} {w['wind_unit']} {w['wind_dir']}") if w else ("--",) * 4
        for value, (x, y, cap, max_w) in zip(values, L["values"]):
            t = ui.text_fit(value, ui.LABEL_MED, self.S(cap), PAPER, self.S(max_w), tracking=1)
            surf.blit(t, t.get_rect(midleft=self.P(x, y)))
        if L["labels"]:                                   # portrait draws its own labels, rule and slogan
            for x, y, label in L["labels"]:
                t = ui.text_fit(label, ui.LABEL, 28, PAPER, 240, tracking=3)
                surf.blit(t, t.get_rect(midleft=self.P(x, y)))
        if L["rule"]:
            (x0, y0), (x1, y1) = L["rule"]
            pygame.draw.line(surf, AMBER, self.P(x0, y0), self.P(x1, y1), 3)
        if L["slogan"]:
            x, y, text = L["slogan"]
            pygame.draw.line(surf, AMBER, (x - 300, y - 50), (x + 300, y - 50), 1)
            t = ui.text(text, ui.LABEL_MED, 30, PAPER, tracking=9)
            surf.blit(t, t.get_rect(center=(x, y)))
        return surf

    # ---- per frame --------------------------------------------------------------------
    def _draw_meteor(self, surf, t):
        SKY, LEN, TIME = self.L["sky"], self.METEOR_LEN, self.METEOR_TIME
        if self.next_meteor is None or self.next_meteor - t > self.METEOR_EVERY[1]:
            self.next_meteor = t + self.rng.uniform(*self.METEOR_EVERY)
        if self.meteor is None and t >= self.next_meteor:
            angle = math.radians(self.rng.uniform(15, 35))
            self.meteor = (t, self.rng.uniform(*self.L["meteor_x"]), self.rng.uniform(50, 130),
                           math.cos(angle) * (1 if self.rng.random() < 0.5 else -1), math.sin(angle))
            self.next_meteor = t + self.rng.uniform(*self.METEOR_EVERY)
        if self.meteor is None:
            return
        start, x0, y0, dx, dy = self.meteor
        k = (t - start) / TIME
        if k >= 1:
            self.meteor = None
            return
        travel = 260
        hx, hy = x0 + dx * travel * k, y0 + dy * travel * k
        fade = math.sin(math.pi * k)
        step = 6
        for i in range(0, LEN, step):          # short segments, brightest at the head
            f = (1 - i / LEN) ** 2 * fade
            a, b = (hx - dx * i, hy - dy * i), (hx - dx * (i + step), hy - dy * (i + step))
            if SKY.collidepoint(a) and SKY.collidepoint(b):
                sky = self.art.get_at((int(a[0]), int(a[1])))
                c = tuple(max(0, min(255, int(sky[j] + (PAPER[j] - sky[j]) * f))) for j in range(3))
                pygame.draw.line(surf, c, a, b, 2 if i < LEN // 3 else 1)

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
