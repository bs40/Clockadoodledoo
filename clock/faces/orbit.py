"""Earth-orbit console face: flip-clock hours, minutes and seconds, with date, weather and
readings panels and a globe.

The background is retface2.png with its baked-in readouts painted out by tools/prep_orbit.py.
On top of that the face draws the live values and animates:
  - the digit cards flip over like a split-flap clock when they change
  - a satellite laps the globe once a minute, passing behind it (it is at the far right on :00)
  - the two cross-hair markers pulse slowly

Landscape positions are in retface2.png pixels, mapped onto the letterboxed background; the
portrait background is composed of three pieces of the poster (globe, title bar, digit panels),
each with its own mapping, and the face draws the lower panels itself.
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

GLOBE = (1535, 312, 217)                 # centre x, y, radius, in poster pixels
ORBIT = (1540, 345, 283, 178)            # the dotted orbit: centre x, y, radius x, radius y


def _map(sx, sy, k, ox, oy):
    """Poster pixels -> canvas pixels for a piece of the poster cut at (sx, sy), scaled by k
    and placed at (ox, oy)."""
    return lambda x, y: (round(ox + (x - sx) * k), round(oy + (y - sy) * k))


def _identity(x, y):
    return x, y


LAYOUTS = {
    "landscape": dict(
        size=(1600, 720), image="background.png",
        globe=_map(0, 0, K, 0, Y0), bar=_map(0, 0, K, 0, Y0), cards=_map(0, 0, K, 0, Y0), digit_k=K,
        text=_map(0, 0, K, 0, Y0), crosshairs=((1265, 100), (1575, 643)), panels=None, frame=None,
        lat=(688, 96, 23, 260), lon=(1005, 96, 23, 260),
        day=(100, 603, 48, 330), date=(100, 669, 39, 310), icon=(636, 638, 104),
        temp=(750, 608, 46, 165), summary=(755, 672, 22, 165), room=(755, 716, 20, 165),
        readings=[(None, 1283, y, 25, 150) for y in (580, 641, 706)], slogan=None,
    ),
    "portrait": dict(
        size=(720, 1600), image="portrait.png",
        globe=_map(1215, 30, 0.9905, 0, 0), bar=_map(40, 50, 0.6207, 0, 500), cards=_map(40, 150, 0.6207, 0, 560),
        digit_k=0.6207, text=_identity, crosshairs=((1265, 100),),
        panels=(pygame.Rect(30, 810, 320, 230), pygame.Rect(370, 810, 320, 230), pygame.Rect(30, 1060, 660, 250)),
        frame=pygame.Rect(6, 6, 708, 1588),
        lat=(688, 96, 16, 200), lon=(1005, 96, 16, 200),
        day=(56, 870, 52, 280), date=(56, 962, 36, 280), icon=(450, 900, 100),
        temp=(520, 875, 44, 160), summary=(520, 940, 20, 160), room=(520, 990, 20, 160),
        readings=[(label, 340, y, 26, 300) for label, y in (("WIND", 1110), ("HUMIDITY", 1185), ("PRESSURE", 1260))],
        slogan=((360, 1400, "A CALMER PLANET"), (360, 1442, "IS A BRIGHTER TOMORROW")),
    ),
}


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
    sizes = {name: layout["size"] for name, layout in LAYOUTS.items()}

    def __init__(self, ctx):
        self.ctx = ctx
        self.L = L = LAYOUTS[ctx.orientation]
        path = ui.ASSETS / "faces" / "orbit" / L["image"]
        self.art = pygame.image.load(str(path)).convert()
        self.static = None
        self.static_key = None
        if L["panels"]:
            self._draw_panels()

        def R(x0, y0, x1, y1):
            (ax, ay), (bx, by) = L["cards"](x0, y0), L["cards"](x1, y1)
            return pygame.Rect(ax, ay, bx - ax, by - ay)
        self.card_rects = [R(*c) for c in CARDS]
        self.grain = pygame.image.frombuffer(os.urandom(256 * 256), (256, 256), "P")
        self.grain.set_palette([(v, v, v) for v in range(256)])
        self.grain = self.grain.convert()
        self.grain.set_alpha(9)
        # Russo One is wider than the mockup's digits, so they are drawn full height and
        # narrowed to fit the slimmest panel.
        self.digit_size = ui.size_for_cap(RUSSO, round(DIGIT_CAP * L["digit_k"]))
        natural = ui.fixed_digits("00", RUSSO, self.digit_size, PAPER)[1].width
        self.digit_squeeze = min(min(r.width for r in self.card_rects) * DIGIT_FILL / natural, 1.0)
        self.cards = {}

        self.satellite = _satellite(10)
        self.crosshair = _crosshair(30)

    def _draw_panels(self):
        """Portrait: the poster's lower panels, redrawn in its style below the cut-out pieces."""
        art, L = self.art, self.L
        pygame.draw.rect(art, (150, 150, 140), L["frame"], 5, border_radius=40)
        for rect in L["panels"]:
            pygame.draw.rect(art, (3, 30, 36), rect, border_radius=16)
            pygame.draw.rect(art, (60, 150, 170), rect, 2, border_radius=16)
        readings = L["panels"][2]
        for y in (1147, 1222):
            pygame.draw.line(art, (40, 100, 115), (readings.x + 32, y), (readings.right - 32, y), 1)

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
            at = (w // 2 - narrow[0] // 2, h // 2 + round(DIGIT_DROP * self.L["digit_k"]) - ink.centery)
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
        L, surf = self.L, self.art.copy()
        T = L["text"]

        loc = self.ctx.config["location"]
        lat = f"LAT {abs(loc['latitude']):.2f}° {'N' if loc['latitude'] >= 0 else 'S'}"
        lon = f"LON {abs(loc['longitude']):.2f}° {'E' if loc['longitude'] >= 0 else 'W'}"
        for label, (x, y, cap, max_w) in ((lat, L["lat"]), (lon, L["lon"])):
            t = ui.text_fit(label, ui.LABEL_MED, cap, CYAN, max_w, tracking=5)
            surf.blit(t, t.get_rect(center=L["bar"](x, y)))

        x, y, cap, max_w = L["day"]
        day = ui.text_fit(now.strftime("%a").upper(), RUSSO, cap, RED, max_w, tracking=12)
        surf.blit(day, day.get_rect(midleft=T(x, y)))
        x, y, cap, max_w = L["date"]
        date = ui.text_fit(now.strftime("%d %b %Y").upper(), ui.LABEL_BOLD, cap, PAPER, max_w, tracking=2)
        surf.blit(date, date.get_rect(midleft=T(x, y)))

        w = self.ctx.readings() or {}
        x, y, size = L["icon"]
        icon = icons.icon(w.get("icon", "sun"), size, AMBER)
        surf.blit(icon, icon.get_rect(center=T(x, y)))
        x, y, cap, max_w = L["temp"]
        temp = ui.text_fit(f"{w['temp']}{w['temp_unit']}" if "temp" in w else "--", ui.LABEL_BOLD, cap, AMBER, max_w, tracking=3)
        surf.blit(temp, temp.get_rect(midleft=T(x, y)))
        x, y, cap, max_w = L["summary"]
        summary = ui.text_fit(w.get("summary", "NO DATA YET"), ui.LABEL_MED, cap, PAPER, max_w, tracking=4)
        surf.blit(summary, summary.get_rect(midleft=T(x, y)))
        if "room_temp" in w:
            x, y, cap, max_w = L["room"]
            room = ui.text_fit(f"ROOM {w['room_temp']:.1f}\u00b0C", ui.LABEL_MED, cap, AMBER, max_w, tracking=3)
            surf.blit(room, room.get_rect(midleft=T(x, y)))

        values = (f"{w['wind']} {w['wind_unit']} {w['wind_dir']}" if "wind" in w else "--",
                  f"{w['humidity']}%" if "humidity" in w else "--", f"{w['pressure']} hPa" if "pressure" in w else "--")
        for value, (label, x, y, cap, max_w) in zip(values, L["readings"]):
            if label:                                  # portrait draws its own labels
                t = ui.text_fit(label, ui.LABEL_MED, cap, PAPER, 240, tracking=3)
                surf.blit(t, t.get_rect(midleft=T(L["panels"][2].x + 32, y)))
            t = ui.text_fit(value, ui.LABEL_MED, cap, PAPER, max_w, tracking=2)
            surf.blit(t, t.get_rect(midleft=T(x, y)))
        if L["slogan"]:
            for x, y, line in L["slogan"]:
                t = ui.text(line, ui.LABEL_MED, 28, AMBER, tracking=6)
                surf.blit(t, t.get_rect(center=(x, y)))
        return surf

    # ---- per frame -----------------------------------------------------------
    def draw(self, surf, now):
        key = (now.strftime("%Y%m%d"), self.ctx.readings_version())
        if key != self.static_key:
            self.static = self._render_static(now)
            self.static_key = key
        surf.blit(self.static, (0, 0))
        t = now.timestamp()

        progress = (now.microsecond / 1e6) / FLIP_TIME
        current, before = self._parts(now), self._parts(now - timedelta(seconds=1))
        for i, rect in enumerate(self.card_rects):
            self._draw_flip(surf, rect, self._card(i, before[i]), self._card(i, current[i]), progress)

        for (x, y), phase in zip(self.L["crosshairs"], (0.0, 0.5)):
            glow = 0.5 - 0.5 * math.cos(2 * math.pi * (t / 8 + phase))
            self.crosshair.set_alpha(round(200 * glow))
            surf.blit(self.crosshair, self.crosshair.get_rect(center=self.L["globe"](x, y)))

        a = 2 * math.pi * ((t % 60) / 60)            # clockwise from the far right, where it sits on :00
        sx, sy = ORBIT[0] + ORBIT[2] * math.cos(a), ORBIT[1] + ORBIT[3] * math.sin(a)
        behind = math.sin(a) < 0 and math.hypot(sx - GLOBE[0], sy - GLOBE[1]) < GLOBE[2] + 6
        if not behind:
            surf.blit(self.satellite, self.satellite.get_rect(center=self.L["globe"](sx, sy)))
