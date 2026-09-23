"""Earth-orbit console face: flip-clock hours, minutes and seconds, with date, weather and
readings panels and a globe.

The background is retface2.png with its baked-in readouts painted out by tools/prep_orbit.py.
On top of that the face draws the live values and animates:
  - the digit cards flip over like a split-flap clock when they change
  - a satellite laps the globe once a minute, passing behind it (it is at the far right on :00)
  - the two cross-hair markers pulse slowly

Positions below are in retface2.png pixels; P() and R() convert them to screen pixels.
"""
import math
import os
from datetime import timedelta

import pygame

from .. import icons, ui

W, H = 1600, 720
K = 1600 / 1942
Y0 = (H - 809 * K) / 2

PAPER = (250, 238, 205)
CYAN = (122, 214, 228)
AMBER = (250, 186, 92)
RED = (240, 78, 48)
RUSSO = "RussoOne-Regular"

CARDS = ((53, 168, 406, 453), (435, 168, 804, 453), (835, 168, 1186, 453))   # hours, minutes, seconds
DIGIT_CAP = 199            # height of the mockup's digits
DIGIT_DROP = 12            # they sit this far below the middle of their panel
DIGIT_FILL = 0.76          # share of a panel's width that two digits take up
FLIP_TIME = 0.24

GLOBE = (1535, 312, 217)                 # centre x, y, radius
ORBIT = (1540, 345, 283, 178)            # the dotted orbit: centre x, y, radius x, radius y
CROSSHAIRS = ((1265, 100), (1575, 643))


def P(x, y):
    return round(x * K), round(Y0 + y * K)


def R(x0, y0, x1, y1):
    (ax, ay), (bx, by) = P(x0, y0), P(x1, y1)
    return pygame.Rect(ax, ay, bx - ax, by - ay)


def _satellite(radius):
    k = 6
    side = (radius * 2 + 4) * k
    surf = pygame.Surface((side, side), pygame.SRCALPHA)
    c = side // 2
    pygame.draw.circle(surf, (8, 22, 30), (c + k, c + k), radius * k)
    pygame.draw.circle(surf, (246, 196, 132), (c, c), radius * k)
    shade = pygame.Surface((side, side), pygame.SRCALPHA)
    shade.fill((150, 140, 140, 255))
    pygame.draw.circle(shade, (255, 255, 255, 255), (c - radius * k // 3, c - radius * k // 4), int(radius * k * 1.02))
    surf.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return pygame.transform.smoothscale(surf, (side // k, side // k))


def _crosshair(arm):
    k = 4
    side = (arm * 2 + 6) * k
    surf = pygame.Surface((side, side), pygame.SRCALPHA)
    c = side // 2
    for width, alpha in ((5 * k, 40), (3 * k, 90), (k, 255)):
        pygame.draw.line(surf, (*CYAN, alpha), (c - arm * k, c), (c + arm * k, c), width)
        pygame.draw.line(surf, (*CYAN, alpha), (c, c - arm * k), (c, c + arm * k), width)
    return pygame.transform.smoothscale(surf, (side // k, side // k))


class OrbitFace:
    name = "orbit"
    size = (W, H)

    def __init__(self, ctx):
        self.ctx = ctx
        path = ui.ASSETS / "faces" / "orbit" / "background.png"
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None

        self.card_rects = [R(*c) for c in CARDS]
        self.grain = pygame.image.frombuffer(os.urandom(256 * 256), (256, 256), "P")
        self.grain.set_palette([(v, v, v) for v in range(256)])
        self.grain = self.grain.convert()
        self.grain.set_alpha(9)
        # Russo One is wider than the mockup's digits, so they are drawn full height and
        # narrowed to fit the slimmest panel.
        self.digit_size = ui.size_for_cap(RUSSO, round(DIGIT_CAP * K))
        natural = ui.fixed_digits("00", RUSSO, self.digit_size, PAPER)[1].width
        self.digit_squeeze = min(min(r.width for r in self.card_rects) * DIGIT_FILL / natural, 1.0)
        self.cards = {}

        self.satellite = _satellite(10)
        self.crosshair = _crosshair(30)

    # ---- flip-clock cards --------------------------------------------------
    def _card(self, index, text):
        key = (index, text)
        if key not in self.cards:
            if len(self.cards) > 140:
                self.cards.clear()
            w, h = self.card_rects[index].size
            card = pygame.Surface((w, h))
            for y in range(h):
                t = min(y / (h * 0.35), 1.0)
                pygame.draw.line(card, (round(4 - 4 * t), round(33 - 11 * t), round(39 - 12 * t)), (0, y), (w, y))
            for x in range(0, w, 256):
                for y in range(0, h, 256):
                    card.blit(self.grain, (x, y))
            digits, ink, _ = ui.fixed_digits(text, RUSSO, self.digit_size, PAPER)
            shadow = ui.fixed_digits(text, RUSSO, self.digit_size, (0, 6, 10))[0]
            narrow = (round(digits.get_width() * self.digit_squeeze), digits.get_height())
            digits = pygame.transform.smoothscale(digits, narrow)
            shadow = pygame.transform.smoothscale(shadow, narrow)
            at = (w // 2 - narrow[0] // 2, h // 2 + round(DIGIT_DROP * K) - ink.centery)
            shadow.set_alpha(170)
            card.blit(shadow, (at[0] - 9, at[1] - 6))
            card.blit(ui.distress(digits, index + 1), at)
            pygame.draw.line(card, (0, 10, 14), (0, h // 2), (w, h // 2), 2)   # the split between the flaps
            self.cards[key] = card
        return self.cards[key]

    @staticmethod
    def _draw_flip(surf, rect, old, new, progress):
        w, h = rect.size
        half = h // 2
        if progress >= 1 or old is new:
            surf.blit(new, rect)
            return
        surf.blit(new, rect.topleft, (0, 0, w, half))                 # the new top, revealed behind the flap
        surf.blit(old, (rect.x, rect.y + half), (0, half, w, h - half))
        if progress < 0.5:                                            # old top half falls towards us
            k = 1 - 2 * progress
            tall = max(round(half * k), 1)
            flap = pygame.transform.smoothscale(old.subsurface((0, 0, w, half)), (w, tall))
            at = (rect.x, rect.y + half - tall)
        else:                                                         # and lands as the new bottom half
            k = 2 * progress - 1
            tall = max(round((h - half) * k), 1)
            flap = pygame.transform.smoothscale(new.subsurface((0, half, w, h - half)), (w, tall))
            at = (rect.x, rect.y + half)
        light = round(255 * (0.5 + 0.5 * k))
        flap.fill((light, light, light), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(flap, at)

    def _parts(self, moment):
        hours = moment.strftime("%H" if self.ctx.config["clock"]["24_hour"] else "%I")
        return hours, moment.strftime("%M"), moment.strftime("%S")

    # ---- layer that only changes with the date or the weather ---------------
    def _render_static(self, now):
        surf = self.art.copy()

        loc = self.ctx.config["location"]
        lat = f"LAT {abs(loc['latitude']):.2f}° {'N' if loc['latitude'] >= 0 else 'S'}"
        lon = f"LON {abs(loc['longitude']):.2f}° {'E' if loc['longitude'] >= 0 else 'W'}"
        for label, x in ((lat, 688), (lon, 1005)):
            t = ui.text_fit(label, ui.LABEL_MED, 23, CYAN, 260, tracking=5)
            surf.blit(t, t.get_rect(center=P(x, 96)))

        day = ui.text_fit(now.strftime("%a").upper(), RUSSO, round(58 * K), RED, 330, tracking=12)
        surf.blit(day, day.get_rect(midleft=P(100, 603)))
        date = ui.text_fit(now.strftime("%d %b %Y").upper(), ui.LABEL_BOLD, round(47 * K), PAPER, 310, tracking=2)
        surf.blit(date, date.get_rect(midleft=P(100, 669)))

        w = self.ctx.weather.current
        icon = icons.icon(w["icon"] if w else "sun", 104, AMBER)
        surf.blit(icon, icon.get_rect(center=P(636, 638)))
        temp = ui.text_fit(f"{w['temp']}{w['temp_unit']}" if w else "--", ui.LABEL_BOLD, round(56 * K), AMBER, 165, tracking=3)
        surf.blit(temp, temp.get_rect(midleft=P(750, 608)))
        summary = ui.text_fit(w["summary"] if w else "NO DATA YET", ui.LABEL_MED, 22, PAPER, 165, tracking=4)
        surf.blit(summary, summary.get_rect(midleft=P(755, 682)))

        values = (f"{w['wind']} {w['wind_unit']} {w['wind_dir']}", f"{w['humidity']}%", f"{w['pressure']} hPa") \
            if w else ("--", "--", "--")
        for value, y in zip(values, (580, 641, 706)):
            t = ui.text_fit(value, ui.LABEL_MED, 25, PAPER, 150, tracking=2)
            surf.blit(t, t.get_rect(midleft=P(1283, y)))
        return surf

    # ---- per frame -----------------------------------------------------------
    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d"), self.ctx.weather.version)
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()

        progress = (now.microsecond / 1e6) / FLIP_TIME
        current, before = self._parts(now), self._parts(now - timedelta(seconds=1))
        for i, rect in enumerate(self.card_rects):
            self._draw_flip(surf, rect, self._card(i, before[i]), self._card(i, current[i]), progress)

        for (x, y), phase in zip(CROSSHAIRS, (0.0, 0.5)):
            glow = 0.5 - 0.5 * math.cos(2 * math.pi * (t / 8 + phase))
            self.crosshair.set_alpha(round(200 * glow))
            surf.blit(self.crosshair, self.crosshair.get_rect(center=P(x, y)))

        a = 2 * math.pi * ((t % 60) / 60)            # clockwise from the far right, where it sits on :00
        sx, sy = ORBIT[0] + ORBIT[2] * math.cos(a), ORBIT[1] + ORBIT[3] * math.sin(a)
        behind = math.sin(a) < 0 and math.hypot(sx - GLOBE[0], sy - GLOBE[1]) < GLOBE[2] + 6
        if not behind:
            surf.blit(self.satellite, self.satellite.get_rect(center=P(sx, sy)))
