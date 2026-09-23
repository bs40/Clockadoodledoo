"""Shared drawing helpers: palette, fonts, tracked text."""
import random
from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Retro print palette shared by all faces.
INK = (11, 22, 30)
CREAM = (239, 230, 208)
MUTED = (146, 160, 160)
LINE = (44, 70, 82)
AMBER = (243, 186, 96)
RED = (214, 72, 44)

WIDE = "Michroma-Regular"
LABEL = "BarlowCondensed-Regular"
LABEL_MED = "BarlowCondensed-Medium"
LABEL_BOLD = "BarlowCondensed-SemiBold"

_fonts = {}
_text_cache = {}


def font(name, size):
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = pygame.font.Font(str(ASSETS / "fonts" / f"{name}.ttf"), size)
    return _fonts[key]


def text(s, name, size, color, tracking=0):
    """Render a line of text, optionally letter-spaced by `tracking` pixels."""
    key = (s, name, size, color, tracking)
    if key in _text_cache:
        return _text_cache[key]
    f = font(name, size)
    if not tracking:
        surf = f.render(s, True, color)
    else:
        glyphs = [f.render(ch, True, color) for ch in s]
        width = sum(g.get_width() for g in glyphs) + tracking * max(len(s) - 1, 0)
        surf = pygame.Surface((max(width, 1), f.get_height()), pygame.SRCALPHA)
        x = 0
        for g in glyphs:
            surf.blit(g, (x, 0))
            x += g.get_width() + tracking
    if len(_text_cache) > 400:
        _text_cache.clear()
    _text_cache[key] = surf
    return surf


def size_for_cap(name, cap_px):
    """Font size whose capitals/digits come out `cap_px` pixels tall."""
    probe = font(name, 200).render("0", True, (255, 255, 255))
    return max(round(200 * cap_px / probe.get_bounding_rect().height), 6)


def text_fit(s, name, cap_px, color, max_width, tracking=0):
    """Text with capitals `cap_px` tall, shrunk if needed to fit `max_width`; cropped to its ink."""
    while True:
        surf = text(s, name, size_for_cap(name, cap_px), color, tracking)
        ink = surf.get_bounding_rect()
        if ink.width <= max_width or cap_px <= 8:
            return surf.subsurface(ink)
        cap_px -= 1


def fixed_digits(s, name, size, color):
    """Render `s` with every digit centred in an equal-width cell, so the text doesn't shift
    as digits change. Returns (surface, ink, spans): `ink` is a rect that stays the same
    whatever the digits are, `spans` is the (x, width) of each character."""
    key = ("fixed", s, name, size, color)
    if key not in _text_cache:
        f = font(name, size)
        cell = max(f.size(d)[0] for d in "0123456789")
        widths = [cell if ch.isdigit() else f.size(ch)[0] for ch in s]
        surf = pygame.Surface((sum(widths), f.get_height()), pygame.SRCALPHA)
        spans, x = [], 0
        for ch, w in zip(s, widths):
            glyph = f.render(ch, True, color)
            surf.blit(glyph, (x + (w - glyph.get_width()) // 2, 0))
            spans.append((x, w))
            x += w
        tall = f.render("0123456789", True, color).get_bounding_rect()
        ink = pygame.Rect(0, tall.y, surf.get_width(), tall.height)
        _text_cache[key] = (surf, ink, spans)
    return _text_cache[key]


def distress(surf, seed):
    """Knock tiny flecks out of `surf` so lettering looks printed, like the poster's own."""
    rng = random.Random(seed)
    w, h = surf.get_size()
    flecks = pygame.Surface((w, h), pygame.SRCALPHA)
    flecks.fill((255, 255, 255, 255))
    for _ in range(w * h // 260):
        flecks.set_at((rng.randrange(w), rng.randrange(h)), (255, 255, 255, rng.randrange(90, 200)))
    for _ in range(w * h // 5000):
        pygame.draw.circle(flecks, (255, 255, 255, rng.randrange(60, 160)),
                           (rng.randrange(w), rng.randrange(h)), rng.choice((1, 1, 2)))
    out = surf.copy()
    out.blit(flecks, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def blit_text(dest, s, name, size, color, pos, tracking=0, anchor="topleft"):
    surf = text(s, name, size, color, tracking)
    rect = surf.get_rect(**{anchor: pos})
    dest.blit(surf, rect)
    return rect
