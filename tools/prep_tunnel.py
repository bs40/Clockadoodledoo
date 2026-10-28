r"""Turn the flower-tunnel mockup into the tunnel face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all
of them live) and letterboxes to 1600x720. Behind the readouts lies dark, heavily blurred
bokeh (teal at the top, plum and the edge of a big orange flower lower down), so the lettering
and its soft glow are inpainted with prep_colony's inpaint(): a smooth surface joining the
hole's edges with the fine grain of the clean picture nearby laid over it.

The 720x1600 portrait version puts the tunnel, its light and the reflection on the water on
top and, below it, the cleared column and its mirror image as a card for the readouts, the
art fading softly into the card.

    .venv\Scripts\python.exe tools\prep_tunnel.py
"""
from pathlib import Path

import random

import pygame

from poster import PORTRAIT, letterbox
from prep_colony import inpaint

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "psychedelic_clock_03_flower_tunnel.png"
FACE = ROOT / "assets" / "faces" / "tunnel"
MATTE = (6, 10, 12)
WIDTH = 2000

TUNNEL = (967, 10, 731, 812)        # portrait: the tunnel, its light and the water (poster px)
COLUMN = (18, 10, 330, 775)         # portrait: the cleared column, mirrored beside itself
TOP, FADE = 800, 130                # the tunnel's height on the portrait, and its fade into the card


def is_cream(r, g, b):
    """The cream time and date (their thin teal glow goes with the grown halo); not the dark
    bokeh or the teal flower beside the time."""
    return r > 140 and g > 130 and b > 100 and abs(r - g) < 45


def is_coral(r, g, b):
    """The coral values and icons: not the plum or pink bokeh (bluer), the dimmer salmon blobs
    of light beside them or orange petals (no blue)."""
    return r > 205 and 85 < g < 190 and b > 65 and g >= b - 12 and r - g > 45


def soften(poster, rect, before, blur=6, grain=4, seed=3):
    """The bokeh is out of focus, so the inpainted pixels of `rect` (those that differ from
    `before`, the region as it was) are eased towards a blurred copy, which melts the odd dark
    fleck the borrowed detail brings with it, and given a fine even grain like the print's."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    area = poster.subsurface((x0, y0, w, h))
    now, was = pygame.image.tobytes(area, "RGB"), pygame.image.tobytes(before, "RGB")
    mask = pygame.Surface((w, h))
    for i in range(w * h):
        if now[i * 3:i * 3 + 3] != was[i * 3:i * 3 + 3]:
            mask.set_at((i % w, i // w), (255, 255, 255))
    small = (max(w // 4, 1), max(h // 4, 1))
    soft = pygame.image.tobytes(pygame.transform.smoothscale(pygame.transform.smoothscale(mask, small), (w, h)), "RGB")
    small = (max(w // blur, 1), max(h // blur, 1))
    blurred = pygame.image.tobytes(pygame.transform.smoothscale(pygame.transform.smoothscale(area, small), (w, h)), "RGB")
    rng, out = random.Random(seed), bytearray(now)
    for i in range(w * h):
        k = min(soft[i * 3] * 2, 255) / 255 * 0.85            # full strength well inside the holes
        if k <= 0:
            continue
        n = rng.uniform(-grain, grain)
        for c in range(3):
            j = i * 3 + c
            out[j] = max(0, min(255, round(now[j] + (blurred[j] + n - now[j]) * k)))
    poster.blit(pygame.image.frombytes(bytes(out), (w, h), "RGB"), (x0, y0))


def clear(poster, rect, wanted, grow, seed=7):
    """inpaint() the lettering in `rect`, then soften() the result."""
    before = poster.subsurface((rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])).copy()
    inpaint(poster, rect, wanted, grow=grow, seed=seed)
    soften(poster, rect, before, seed=seed)


def build():
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    clear(poster, (66, 36, 700, 258), is_cream, grow=9)                  # the time
    clear(poster, (80, 262, 604, 342), is_cream, grow=8, seed=8)         # the date
    clear(poster, (70, 362, 372, 800), is_coral, grow=8, seed=9)         # icons and values
    letterbox(poster, FACE / "background.png", MATTE)
    return poster


def portrait(cleaned, out):
    canvas = pygame.Surface(PORTRAIT)
    canvas.fill(MATTE)
    card_h = PORTRAIT[1] - TOP + FADE
    card = pygame.transform.smoothscale(cleaned.subsurface(COLUMN), (360, card_h))
    canvas.blit(card, (0, TOP - FADE))
    canvas.blit(pygame.transform.flip(card, True, False), (360, TOP - FADE))
    art = pygame.transform.smoothscale(cleaned.subsurface(TUNNEL), (PORTRAIT[0], TOP)).convert_alpha()
    ramp = pygame.Surface(art.get_size(), pygame.SRCALPHA)
    ramp.fill((255, 255, 255, 255))
    for y in range(FADE):                                    # ease the art out over the card
        k = (y + 0.5) / FADE
        ramp.fill((255, 255, 255, round(255 * (1 - k * k * (3 - 2 * k)))), (0, TOP - FADE + y, PORTRAIT[0], 1))
    art.blit(ramp, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    canvas.blit(art, (0, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    cleaned = build()
    portrait(cleaned, FACE / "portrait.png")
