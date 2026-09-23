"""Pixel-art rainy city face: date, time and weather in a dark panel on the right.

The background is pixface1.png with its baked-in readouts painted out by tools/prep_pixel.py.
Animation: rain falls over the city, the neon ramen sign and the lantern flicker now and then,
the pixel weather icon animates (falling drops, drifting cloud, spinning sun) and the colon
blinks on odd seconds.
"""
import math
import random

import pygame

from .. import ui

W, H = 1600, 720
K = 1600 / 1944
Y0 = (H - 809 * K) / 2

CREAM = (238, 226, 184)
CYAN = (176, 236, 230)
PIXEL_BIG = "PressStart2P-Regular"
PIXEL = "Silkscreen-Regular"

DATE_POS, DATE_CAP = (1410, 92), 36
TIME_CX, TIME_Y, TIME_CAP, TIME_MAX_W = 1640, 215, 132, 455
ICON_CENTRE, ICON_CELL = (1500, 395), 9            # icon grid cell size, in retface pixels
TEMP_POS, TEMP_CAP = (1620, 362), 54
SUMMARY_POS, SUMMARY_CAP = (1620, 436), 28
VALUE_X, VALUE_CAP, VALUE_YS = 1665, 28, (573, 632, 688)

CITY = pygame.Rect(20, 40, 1090, 620)             # where rain falls, in background.png pixels
RAIN_DROPS = 70
NEON = (pygame.Rect(150, 145, 212, 152), pygame.Rect(378, 205, 95, 205))   # ramen sign, lantern

# Pixel icons on a 14x12 grid. Letters pick colours; '.' is empty.
PALETTE = {"c": (206, 232, 230), "d": (160, 196, 200), "b": (110, 200, 236), "y": (250, 214, 96),
           "o": (250, 160, 70), "w": (240, 244, 250), "g": (150, 160, 170), "e": (250, 236, 120)}
ICONS = {
    "sun": ["......y.......", "..y...y...y...", "...y.yyy.y....", "....yyyyy.....", ".yyyyyeeyyyy..",
            "....yyeeeyy...", ".yyyyyeeyyyy..", "....yyyyy.....", "...y.yyy.y....", "..y...y...y...",
            "......y.......", ".............."],
    "cloud": ["..............", ".....cccc.....", "....cccccc....", "..cccccccccc..", ".cccccccccccc.",
              ".cccccccccccc.", "..dddddddddd..", "..............", "..............", "..............",
              "..............", ".............."],
    "partly": ["....y.........", ".y..yyy..y....", "...yyeyy......", "..yyeeeyy.....", "...yycccc.....",
               ".y..cccccc....", "..cccccccccc..", ".cccccccccccc.", "..dddddddddd..", "..............",
               "..............", ".............."],
    "rain": ["..............", ".....cccc.....", "....cccccc....", "..cccccccccc..", ".cccccccccccc.",
             "..dddddddddd..", "..............", "...b...b...b..", "..b...b...b...", "..............",
             "...b...b...b..", "..b...b...b..."],
    "snow": ["..............", ".....cccc.....", "....cccccc....", "..cccccccccc..", ".cccccccccccc.",
             "..dddddddddd..", "..............", "...w...w...w..", "..............", ".....w...w....",
             "..............", "...w...w...w.."],
    "storm": ["..............", ".....gggg.....", "....gggggg....", "..gggggggggg..", ".gggggggggggg.",
              "..gggggggggg..", "......ee......", ".....ee.......", "....eeee......", "......ee......",
              ".....ee.......", "....e........."],
    "fog": ["..............", "..gggggggg....", "..............", "....gggggggg..", "..............",
            "..gggggggg....", "..............", "....gggggggg..", "..............", "..gggggggg....",
            "..............", ".............."],
}
ICONS["clear-night"] = ICONS["sun"]


def P(x, y):
    return round(x * K), round(Y0 + y * K)


def _icon_surface(name, frame):
    rows = [list(r) for r in ICONS.get(name, ICONS["cloud"])]
    if name in ("rain", "snow"):                  # the drops fall: cycle the lower rows
        lower = rows[7:]
        shift = frame % len(lower)
        rows = rows[:7] + lower[-shift:] + lower[:-shift] if shift else rows
    elif name == "fog":
        rows = [[*r[1:], r[0]] if (i // 2 + frame) % 2 else r for i, r in enumerate(rows)]
    elif name in ("sun", "clear-night") and frame % 2:
        rows = [list(r.replace("y", "e") if False else r) for r in ICONS[name]]
        rows = [[("y" if c == "e" and (i + j) % 2 else c) for j, c in enumerate(r)] for i, r in enumerate(rows)]
    h, w = len(rows), len(rows[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in PALETTE:
                surf.set_at((x, y), PALETTE[ch])
    cell = round(ICON_CELL * K)
    return pygame.transform.scale(surf, (w * cell, h * cell))


class PixelFace:
    name = "pixel"
    size = (W, H)

    def __init__(self, ctx):
        self.ctx = ctx
        path = ui.ASSETS / "faces" / "pixel" / "background.png"
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        self.colon = None
        self.icon_name = "cloud"
        self.icons = {}
        rng = random.Random(5)
        self.rain = [[rng.uniform(CITY.left, CITY.right), rng.uniform(CITY.top, CITY.bottom),
                      rng.uniform(420, 620), rng.randint(10, 22)] for _ in range(RAIN_DROPS)]
        self.rain_layer = pygame.Surface(CITY.size, pygame.SRCALPHA)
        self.last_t = None
        self.rng = random.Random()
        self.flicker = [0.0, 0.0]        # end time of the current flicker for each neon region
        self.shade = [pygame.Surface(r.size) for r in NEON]

    # ---- text layer -----------------------------------------------------------------
    def _render_static(self, now):
        surf = self.art.copy()
        date = ui.text_fit(now.strftime("%a %d %b %Y").upper(), PIXEL, round(DATE_CAP * K), CREAM, 400, tracking=3)
        surf.blit(date, date.get_rect(midleft=P(*DATE_POS)))

        clock = now.strftime("%H:%M") if self.ctx.config["clock"]["24_hour"] else now.strftime("%I:%M").lstrip("0")
        full, ink, spans = ui.fixed_digits(clock, PIXEL_BIG, ui.size_for_cap(PIXEL_BIG, round(TIME_CAP * K)), CREAM)
        squeeze = min(TIME_MAX_W * K / ink.width, 1.0)
        x, width = spans[clock.index(":")]
        gap = pygame.Rect(round(x * squeeze), 0, round(width * squeeze), full.get_height())
        full = pygame.transform.scale(full, (round(full.get_width() * squeeze), full.get_height()))
        ink = pygame.Rect(0, ink.y, full.get_width(), ink.height)
        cx, cy = P(TIME_CX, TIME_Y)
        origin = (cx - ink.centerx, cy - ink.centery)
        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

        w = self.ctx.weather.current
        self.icon_name = w["icon"] if w else "cloud"
        temp = ui.text_fit(f"{w['temp']}{w['temp_unit']}" if w else "--", PIXEL, round(TEMP_CAP * K), CREAM, 230, tracking=3)
        surf.blit(temp, temp.get_rect(midleft=P(*TEMP_POS)))
        summary = ui.text_fit(w["summary"] if w else "NO DATA YET", PIXEL, round(SUMMARY_CAP * K), CREAM, 240, tracking=3)
        surf.blit(summary, summary.get_rect(midleft=P(*SUMMARY_POS)))
        values = (f"{w['humidity']}%", f"{w['wind']} {w['wind_unit']} {w['wind_dir']}", f"{w['pressure']} hPa") \
            if w else ("--",) * 3
        for value, y in zip(values, VALUE_YS):
            t = ui.text_fit(value, PIXEL, round(VALUE_CAP * K), CYAN, 200, tracking=3)
            surf.blit(t, t.get_rect(midleft=P(VALUE_X, y)))
        return surf

    # ---- per frame ---------------------------------------------------------------------
    def _draw_rain(self, surf, dt):
        layer = self.rain_layer
        layer.fill((0, 0, 0, 0))
        for drop in self.rain:
            drop[1] += drop[2] * dt
            drop[0] -= 40 * dt                      # a little wind
            if drop[1] > CITY.height or drop[0] < 0:
                drop[0], drop[1] = self.rng.uniform(0, CITY.width), -drop[3]
            x, y = drop[0], drop[1]
            pygame.draw.line(layer, (205, 215, 245, 80), (x, y), (x - 1, y + drop[3]), 1)
        surf.blit(layer, CITY.topleft)

    def _draw_neon(self, surf, t):
        for i, rect in enumerate(NEON):
            if t > self.flicker[i]:
                if self.rng.random() < 0.006:       # about one flicker every 5 s at 30 fps
                    self.flicker[i] = t + self.rng.uniform(0.1, 0.45)
                continue
            self.shade[i].set_alpha(self.rng.randint(50, 150))
            surf.blit(self.shade[i], rect)

    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()
        dt = 0.0 if self.last_t is None else min(max(t - self.last_t, 0.0), 0.1)
        self.last_t = t

        self._draw_rain(surf, dt)
        self._draw_neon(surf, t)
        if now.second % 2 == 1:
            surf.blit(*self.colon)
        frame = int(t * 3)
        icon_key = (self.icon_name, frame % 6)
        if icon_key not in self.icons:
            self.icons[icon_key] = _icon_surface(*icon_key)
        icon = self.icons[icon_key]
        surf.blit(icon, icon.get_rect(center=P(*ICON_CENTRE)))
