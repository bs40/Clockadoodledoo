"""Orrery face: time and weather on the left, a toy solar system in the middle.

Earth laps the sun once a minute, starting from the top, so it doubles as a
seconds hand. The other planets keep their real orbital periods relative to it.
"""
import math
import os
import random
from datetime import timezone

import pygame

from .. import astro, icons, ui

W, H = 1600, 720
SS = 2  # oversampling for the static artwork

CENTRE = (930, 300)
FLATTEN = 0.62
LEFT = 110

# name, orbit radius (px), period (years), disc radius (px), colour
PLANETS = (
    ("MERCURY", 75, 0.241, 7, (170, 164, 154)),
    ("VENUS", 120, 0.615, 10, (228, 194, 138)),
    ("EARTH", 170, 1.0, 11, (132, 184, 196)),
    ("MARS", 220, 1.881, 9, (217, 124, 86)),
    ("JUPITER", 290, 11.86, 18, (218, 180, 138)),
    ("SATURN", 360, 29.46, 15, (205, 184, 146)),
)

# Areas kept free of stars so text stays clean: readouts, legend, slogans.
QUIET_ZONES = (pygame.Rect(90, 50, 490, 570), pygame.Rect(1370, 80, 180, 310),
               pygame.Rect(990, 580, 560, 90))

SLOGAN ="A SMALL PART OF A BIG UNIVERSE"


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
    size = (W, H)

    def __init__(self, ctx):
        self.ctx = ctx
        self.art = self._render_art()
        self.sprites = {p[0]: self._planet_sprite(p) for p in PLANETS}
        self.static = None
        self.static_key = None

    # ---- static artwork, rendered once ---------------------------------
    def _render_art(self):
        big = pygame.Surface((W * SS, H * SS))
        big.fill(ui.INK)
        rng = random.Random(1961)
        for _ in range(420):
            x, y = rng.randrange(W * SS), rng.randrange(H * SS)
            if any(r.collidepoint(x // SS, y // SS) for r in QUIET_ZONES):
                continue
            v = rng.choice((70, 95, 120, 170, 230))
            pygame.draw.circle(big, (v, v, int(v * 0.95)), (x, y), rng.choice((1, 1, 2, 2, 3)))

        cx, cy = CENTRE[0] * SS, CENTRE[1] * SS
        reach_x, reach_y = 400 * SS, int(400 * FLATTEN) * SS
        pygame.draw.line(big, ui.LINE, (cx - reach_x, cy), (cx + reach_x, cy), SS)
        pygame.draw.line(big, ui.LINE, (cx, cy - reach_y), (cx, cy + reach_y), SS)
        for i in range(-8, 9):
            pygame.draw.line(big, ui.LINE, (cx + i * 50 * SS, cy - 5 * SS), (cx + i * 50 * SS, cy + 5 * SS), SS)
        for _, radius, *_ in PLANETS:
            rect = pygame.Rect(0, 0, radius * 2 * SS, int(radius * 2 * FLATTEN) * SS)
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

        for i, (name, *_rest, colour) in enumerate(PLANETS):
            y = 100 + i * 52
            earth = name == "EARTH"
            pygame.draw.circle(art, ui.AMBER if earth else colour, (1392, y), 9 if earth else 7)
            ui.blit_text(art, name, ui.LABEL_MED if earth else ui.LABEL, 26,
                         ui.CREAM if earth else ui.MUTED, (1418, y), tracking=4, anchor="midleft")
        ui.blit_text(art, SLOGAN, ui.LABEL, 28, ui.CREAM, (1530, 648), tracking=7, anchor="midright")
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
        surf = self.art.copy()
        if self.ctx.config["clock"]["24_hour"]:
            clock = now.strftime("%H:%M")
        else:
            clock = now.strftime("%I:%M").lstrip("0")
        surf.blit(ui.fixed_digits(clock, ui.WIDE, 112, ui.CREAM)[0], (LEFT - 6, 52))
        ui.blit_text(surf, now.strftime("%a %d %b %Y").upper(), ui.LABEL_MED, 44, ui.CREAM,
                     (LEFT, 196), tracking=6)
        pygame.draw.line(surf, ui.MUTED, (LEFT, 268), (LEFT + 440, 268), 1)
        for i, (icon, value, label) in enumerate(self._rows(now)):
            y = 318 + i * 64
            surf.blit(icon, icon.get_rect(center=(LEFT + 22, y)))
            ui.blit_text(surf, value, ui.LABEL_MED, 40, ui.CREAM, (LEFT + 72, y), anchor="midleft")
            ui.blit_text(surf, label, ui.LABEL, 25, ui.MUTED, (LEFT + 258, y + 2), tracking=4, anchor="midleft")
        ui.blit_text(surf, _greeting(now.hour), ui.LABEL, 28, ui.CREAM, (1530, 600),
                     tracking=7, anchor="midright")
        return surf

    # ---- per frame -------------------------------------------------------
    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d%H%M"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))

        minutes = now.timestamp() / 60
        for name, radius, period, _, _ in PLANETS:
            a = -math.pi / 2 + 2 * math.pi * (minutes / period % 1.0)
            x = CENTRE[0] + radius * math.cos(a)
            y = CENTRE[1] + radius * FLATTEN * math.sin(a)
            sprite = self.sprites[name]
            surf.blit(sprite, sprite.get_rect(center=(round(x), round(y))))
