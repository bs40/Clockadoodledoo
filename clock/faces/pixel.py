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

K = 1600 / 1944
Y0 = (720 - 809 * K) / 2

CREAM = (238, 226, 184)
CYAN = (176, 236, 230)
PIXEL_BIG = "PressStart2P-Regular"
PIXEL = "Silkscreen-Regular"

RAIN_DROPS = 70

# Landscape positions are pixface1.png pixels mapped by P(); portrait ones are canvas pixels.
# Sizes (caps, widths, icon cell) are canvas pixels in both.
LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png", scale=K, offset=(0, Y0), panel=None,
        date=(1410, 92, 30, 400), time=(1640, 215, 109, 375), icon=(1500, 395, 7),
        temp=(1620, 362, 44, 230), summary=(1620, 436, 23, 240), room=(1620, 482, 19, 240),
        values=[(None, 1665, y, 23, 200) for y in (573, 632, 688)], divider=None,
        city=pygame.Rect(20, 40, 1090, 620),
        neon=(pygame.Rect(150, 145, 212, 152), pygame.Rect(378, 205, 95, 205)),   # ramen sign, lantern
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png", scale=1.0, offset=(0, 0), panel=pygame.Rect(24, 830, 672, 746),
        date=(60, 900, 30, 600), time=(360, 1010, 132, 620), icon=(150, 1180, 8),
        temp=(270, 1150, 52, 300), summary=(270, 1222, 26, 400), room=(270, 1268, 20, 400),
        values=[(label, 380, y, 28, 300) for label, y in (("HUMIDITY", 1370), ("WIND", 1440), ("PRESSURE", 1510))],
        divider=(60, 1300, 660),
        city=pygame.Rect(0, 0, 720, 809),
        neon=(pygame.Rect(0, 176, 110, 185), pygame.Rect(129, 216, 115, 249)),
    ),
}

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


def _icon_surface(name, frame, cell):
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
    return pygame.transform.scale(surf, (w * cell, h * cell))


class PixelFace:
    name = "pixel"
    sizes = {name: layout["size"] for name, layout in LAYOUTS.items()}

    def __init__(self, ctx):
        self.ctx = ctx
        self.L = LAYOUTS[ctx.orientation]
        path = ui.ASSETS / "faces" / "pixel" / self.L["image"]
        self.art = pygame.image.load(str(path)).convert()
        if self.L["panel"]:
            self._draw_panel()
        self.static = None
        self.static_key = None
        self.colon = None
        self.icon_name = "cloud"
        self.icons = {}
        rng = random.Random(5)
        CITY = self.L["city"]
        self.rain = [[rng.uniform(0, CITY.width), rng.uniform(0, CITY.height),
                      rng.uniform(420, 620), rng.randint(10, 22)] for _ in range(RAIN_DROPS)]
        self.rain_layer = pygame.Surface(CITY.size, pygame.SRCALPHA)
        self.last_t = None
        self.rng = random.Random()
        self.flicker = [0.0, 0.0]        # end time of the current flicker for each neon region
        self.shade = [pygame.Surface(r.size) for r in self.L["neon"]]

    def P(self, x, y):
        k, (ox, oy) = self.L["scale"], self.L["offset"]
        return round(ox + x * k), round(oy + y * k)

    def _draw_panel(self):
        """Portrait: the dark readout panel, drawn below the street in the poster's style."""
        art, panel = self.art, self.L["panel"]
        pygame.draw.rect(art, (7, 7, 9), panel, border_radius=22)
        rng = random.Random(9)
        for _ in range(panel.width * panel.height // 40):        # a little pixel grain
            x, y = rng.randrange(panel.left + 4, panel.right - 4), rng.randrange(panel.top + 4, panel.bottom - 4)
            v = rng.randint(10, 22)
            art.set_at((x, y), (v, v, v + 2))
        pygame.draw.rect(art, (96, 104, 112), panel, 3, border_radius=22)
        x0, y, x1 = self.L["divider"]
        pygame.draw.line(art, CYAN, (x0, y), (x1, y), 2)
        pygame.draw.polygon(art, CYAN, [(x1 - 100, y), (x1 - 92, y - 6), (x1 - 84, y), (x1 - 92, y + 6)])

    # ---- text layer -----------------------------------------------------------------
    def _render_static(self, now):
        L, surf = self.L, self.art.copy()
        x, y, cap, max_w = L["date"]
        date = ui.text_fit(now.strftime("%a %d %b %Y").upper(), PIXEL, cap, CREAM, max_w, tracking=3)
        surf.blit(date, date.get_rect(midleft=self.P(x, y)))

        clock = now.strftime("%H:%M") if self.ctx.config["clock"]["24_hour"] else now.strftime("%I:%M").lstrip("0")
        tx, ty, cap, max_w = L["time"]
        full, ink, spans = ui.fixed_digits(clock, PIXEL_BIG, ui.size_for_cap(PIXEL_BIG, cap), CREAM)
        squeeze = min(max_w / ink.width, 1.0)
        x, width = spans[clock.index(":")]
        gap = pygame.Rect(round(x * squeeze), 0, round(width * squeeze), full.get_height())
        full = pygame.transform.scale(full, (round(full.get_width() * squeeze), full.get_height()))
        ink = pygame.Rect(0, ink.y, full.get_width(), ink.height)
        cx, cy = self.P(tx, ty)
        origin = (cx - ink.centerx, cy - ink.centery)
        self.colon = (full.subsurface(gap).copy(), (origin[0] + gap.x, origin[1]))
        full.fill((0, 0, 0, 0), gap)
        surf.blit(full, origin)

        w = self.ctx.readings() or {}
        self.icon_name = w.get("icon", "cloud")
        x, y, cap, max_w = L["temp"]
        temp = ui.text_fit(f"{w['temp']}{w['temp_unit']}" if "temp" in w else "--", PIXEL, cap, CREAM, max_w, tracking=3)
        surf.blit(temp, temp.get_rect(midleft=self.P(x, y)))
        x, y, cap, max_w = L["summary"]
        summary = ui.text_fit(w.get("summary", "NO DATA YET"), PIXEL, cap, CREAM, max_w, tracking=3)
        surf.blit(summary, summary.get_rect(midleft=self.P(x, y)))
        if "room_temp" in w:
            x, y, cap, max_w = L["room"]
            room = ui.text_fit(f"ROOM {w['room_temp']:.1f}\u00b0C", PIXEL, cap, CYAN, max_w, tracking=3)
            surf.blit(room, room.get_rect(midleft=self.P(x, y)))
        values = (f"{w['humidity']}%" if "humidity" in w else "--",
                  f"{w['wind']} {w['wind_unit']} {w['wind_dir']}" if "wind" in w else "--",
                  f"{w['pressure']} hPa" if "pressure" in w else "--")
        for value, (label, x, y, cap, max_w) in zip(values, L["values"]):
            if label:                                     # portrait draws its own labels
                t = ui.text_fit(label, PIXEL, cap, CYAN, 300, tracking=3)
                surf.blit(t, t.get_rect(midleft=self.P(60, y)))
            t = ui.text_fit(value, PIXEL, cap, CYAN, max_w, tracking=3)
            surf.blit(t, t.get_rect(midleft=self.P(x, y)))
        return surf

    # ---- per frame ---------------------------------------------------------------------
    def _draw_rain(self, surf, dt):
        CITY, layer = self.L["city"], self.rain_layer
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
        for i, rect in enumerate(self.L["neon"]):
            if t > self.flicker[i]:
                if self.rng.random() < 0.006:       # about one flicker every 5 s at 30 fps
                    self.flicker[i] = t + self.rng.uniform(0.1, 0.45)
                continue
            self.shade[i].set_alpha(self.rng.randint(50, 150))
            surf.blit(self.shade[i], rect)

    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.readings_version())
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
        ix, iy, cell = self.L["icon"]
        icon_key = (self.icon_name, frame % 6)
        if icon_key not in self.icons:
            self.icons[icon_key] = _icon_surface(*icon_key, cell)
        icon = self.icons[icon_key]
        surf.blit(icon, icon.get_rect(center=self.P(ix, iy)))
