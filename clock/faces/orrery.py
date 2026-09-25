"""Orrery face: time and weather beside (landscape) or above (portrait) a toy solar system.

Earth laps the sun once a minute, starting from the top, so it doubles as a
seconds hand. The other planets keep their real orbital periods relative to it.
"""
import math
import os
import random
from datetime import timezone

import pygame

from .. import astro, icons, ui

SS = 2  # oversampling for the static artwork

# name, orbit radius (px), period (years), disc radius (px), colour
PLANETS = (
    ("MERCURY", 75, 0.241, 7, (170, 164, 154)),
    ("VENUS", 120, 0.615, 10, (228, 194, 138)),
    ("EARTH", 170, 1.0, 11, (132, 184, 196)),
    ("MARS", 220, 1.881, 9, (217, 124, 86)),
    ("JUPITER", 290, 11.86, 18, (218, 180, 138)),
    ("SATURN", 360, 29.46, 15, (205, 184, 146)),
)

SLOGAN = "A SMALL PART OF A BIG UNIVERSE"

LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), centre=(930, 300), flatten=0.62, orbit_scale=1.0, reach=400, stars=420,
        quiet=(pygame.Rect(90, 50, 490, 570), pygame.Rect(1370, 80, 180, 310), pygame.Rect(990, 580, 560, 90)),
        legend=[(1392, 100 + i * 52) for i in range(6)],
        time=(104, 52, 112), date=(110, 196), rule=(110, 268, 550), rows=(110, 318, 64),
        greeting=(1530, 600, "midright"), slogan=(1530, 648, "midright"),
    ),
    "portrait": dict(
        size=(720, 1600), centre=(360, 640), flatten=0.72, orbit_scale=0.8, reach=310, stars=360,
        quiet=(pygame.Rect(40, 40, 640, 260), pygame.Rect(40, 900, 640, 660)),
        legend=[(96 + (i % 3) * 200, 940 + (i // 3) * 46) for i in range(6)],
        time=(50, 60, 128), date=(58, 210), rule=(58, 280, 662), rows=(58, 1080, 62),
        greeting=(360, 1500, "center"), slogan=(360, 1546, "center"),
    ),
}


def _greeting(hour):
    if hour < 5:
        return "GOOD NIGHT"
    if hour < 12:
        return "GOOD MORNING"
    if hour < 18:
        return "GOOD AFTERNOON"
    if hour < 22:
        return "GOOD EVENING"
    return "GOOD NIGHT"


class OrreryFace:
    name = "orrery"
    sizes = {name: layout["size"] for name, layout in LAYOUTS.items()}

    def __init__(self, ctx):
        self.ctx = ctx
        self.L = LAYOUTS[ctx.orientation]
        self.W, self.H = self.L["size"]
        self.art = self._render_art()
        self.sprites = {p[0]: self._planet_sprite(p) for p in PLANETS}
        self.static = None
        self.static_key = None

    # ---- static artwork, rendered once ---------------------------------
    def _render_art(self):
        L, W, H = self.L, self.W, self.H
        big = pygame.Surface((W * SS, H * SS))
        big.fill(ui.INK)
        rng = random.Random(1961)
        for _ in range(L["stars"]):
            x, y = rng.randrange(W * SS), rng.randrange(H * SS)
            if any(r.collidepoint(x // SS, y // SS) for r in L["quiet"]):
                continue
            v = rng.choice((70, 95, 120, 170, 230))
            pygame.draw.circle(big, (v, v, int(v * 0.95)), (x, y), rng.choice((1, 1, 2, 2, 3)))

        cx, cy = L["centre"][0] * SS, L["centre"][1] * SS
        flatten, k = L["flatten"], L["orbit_scale"]
        reach_x, reach_y = L["reach"] * SS, int(L["reach"] * flatten) * SS
        pygame.draw.line(big, ui.LINE, (cx - reach_x, cy), (cx + reach_x, cy), SS)
        pygame.draw.line(big, ui.LINE, (cx, cy - reach_y), (cx, cy + reach_y), SS)
        for i in range(-8, 9):
            pygame.draw.line(big, ui.LINE, (cx + i * 50 * SS, cy - 5 * SS), (cx + i * 50 * SS, cy + 5 * SS), SS)
        for _, radius, *_ in PLANETS:
            rect = pygame.Rect(0, 0, int(radius * k * 2) * SS, int(radius * k * 2 * flatten) * SS)
            rect.center = (cx, cy)
            pygame.draw.ellipse(big, (70, 100, 112), rect, SS + 1)

        glow = pygame.Surface((300 * SS, 300 * SS), pygame.SRCALPHA)
        for r in range(150 * SS, 34 * SS, -2):
            t = 1 - (r - 34 * SS) / (116 * SS)
            pygame.draw.circle(glow, (*ui.AMBER, int(70 * t * t)), (150 * SS, 150 * SS), r)
        pygame.draw.circle(glow, (250, 214, 140), (150 * SS, 150 * SS), 34 * SS)
        pygame.draw.circle(glow, (255, 236, 186), (150 * SS, 150 * SS), 22 * SS)
        big.blit(glow, glow.get_rect(center=(cx, cy)))

        frame = pygame.Rect(22 * SS, 22 * SS, (W - 44) * SS, (H - 44) * SS)
        pygame.draw.rect(big, (190, 186, 170), frame, 2 * SS, border_radius=46 * SS)

        art = pygame.transform.smoothscale(big, (W, H))

        # Print grain: a tiled patch of grey noise at low opacity.
        tile = pygame.image.frombuffer(os.urandom(256 * 256), (256, 256), "P")
        tile.set_palette([(v, v, v) for v in range(256)])
        tile = tile.convert()
        tile.set_alpha(12)
        for x in range(0, W, 256):
            for y in range(0, H, 256):
                art.blit(tile, (x, y))

        for (name, *_rest, colour), (x, y) in zip(PLANETS, L["legend"]):
            earth = name == "EARTH"
            pygame.draw.circle(art, ui.AMBER if earth else colour, (x, y), 9 if earth else 7)
            ui.blit_text(art, name, ui.LABEL_MED if earth else ui.LABEL, 26,
                         ui.CREAM if earth else ui.MUTED, (x + 26, y), tracking=4, anchor="midleft")
        sx, sy, anchor = L["slogan"]
        ui.blit_text(art, SLOGAN, ui.LABEL, 28, ui.CREAM, (sx, sy), tracking=7, anchor=anchor)
        return art

    def _planet_sprite(self, planet):
        name, _, _, r, colour = planet
        k = 8
        side = (r * 2 + 24) * k
        surf = pygame.Surface((side, side), pygame.SRCALPHA)
        c = side // 2
        pygame.draw.circle(surf, colour, (c, c), r * k)
        shade = pygame.Surface((side, side), pygame.SRCALPHA)
        shade.fill((120, 120, 130, 255))
        pygame.draw.circle(shade, (255, 255, 255, 255), (c - int(r * k * 0.35), c - int(r * k * 0.3)), int(r * k * 1.05))
        surf.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        if name == "SATURN":
            ring = pygame.Rect(0, 0, int(r * k * 3.4), int(r * k * 1.1))
            ring.center = (c, c)
            pygame.draw.ellipse(surf, (226, 208, 170), ring, k * 2)
        return pygame.transform.smoothscale(surf, (side // k, side // k))

    # ---- text layer, re-rendered when something on it changes ------------
    def _rows(self, now):
        w = self.ctx.weather.current
        dash = "--"
        rows = [
            (icons.icon(w["icon"] if w else "sun", 42, ui.CREAM),
             f"{w['temp']}{w['temp_unit']}" if w else dash, w["summary"] if w else "NO DATA YET"),
            (icons.icon("drop", 42, ui.CREAM), f"{w['humidity']}%" if w else dash, "HUMIDITY"),
            (icons.icon("gauge", 42, ui.CREAM), f"{w['pressure']} hPa" if w else dash, "PRESSURE"),
            (icons.icon("wind", 42, ui.CREAM),
             f"{w['wind']} {w['wind_unit']} {w['wind_dir']}" if w else dash, "WIND"),
        ]
        event = self.ctx.weather.next_sun_event(now.replace(tzinfo=None))
        if event:
            when, kind = event
            rows.append((icons.icon(kind, 42, ui.CREAM), when.strftime("%H:%M"), kind.upper()))
        phase, illum, name = astro.moon_phase(now.astimezone(timezone.utc))
        rows.append((icons.moon(phase, 42, ui.CREAM, (52, 66, 74)), f"{round(illum * 100)}%", name))
        return rows

    def _render_static(self, now):
        L = self.L
        surf = self.art.copy()
        if self.ctx.config["clock"]["24_hour"]:
            clock = now.strftime("%H:%M")
        else:
            clock = now.strftime("%I:%M").lstrip("0")
        tx, ty, tsize = L["time"]
        surf.blit(ui.fixed_digits(clock, ui.WIDE, tsize, ui.CREAM)[0], (tx, ty))
        ui.blit_text(surf, now.strftime("%a %d %b %Y").upper(), ui.LABEL_MED, 44, ui.CREAM, L["date"], tracking=6)
        rx, ry, rx1 = L["rule"]
        pygame.draw.line(surf, ui.MUTED, (rx, ry), (rx1, ry), 1)
        left, top, step = L["rows"]
        for i, (icon, value, label) in enumerate(self._rows(now)):
            y = top + i * step
            surf.blit(icon, icon.get_rect(center=(left + 22, y)))
            ui.blit_text(surf, value, ui.LABEL_MED, 40, ui.CREAM, (left + 72, y), anchor="midleft")
            ui.blit_text(surf, label, ui.LABEL, 25, ui.MUTED, (left + 258, y + 2), tracking=4, anchor="midleft")
        gx, gy, anchor = L["greeting"]
        ui.blit_text(surf, _greeting(now.hour), ui.LABEL, 28, ui.CREAM, (gx, gy), tracking=7, anchor=anchor)
        return surf

    # ---- per frame -------------------------------------------------------
    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))

        L = self.L
        minutes = now.timestamp() / 60
        for name, radius, period, _, _ in PLANETS:
            a = -math.pi / 2 + 2 * math.pi * (minutes / period % 1.0)
            x = L["centre"][0] + radius * L["orbit_scale"] * math.cos(a)
            y = L["centre"][1] + radius * L["orbit_scale"] * L["flatten"] * math.sin(a)
            sprite = self.sprites[name]
            surf.blit(sprite, sprite.get_rect(center=(round(x), round(y))))
