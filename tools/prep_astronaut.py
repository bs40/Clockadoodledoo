r"""Turn the astronaut mockup into the astronaut face's backgrounds (landscape and portrait).

Covers the baked-in date, time and the weather column (icons, values and labels: the face
draws all of them live) with plain paper copied from clean corners of the cream panel, woven
from soft-edged tiles so no block edges show, then evens out the new paper's light and shade
to match the panel's own. Letterboxes to 1600x720, and composes a 720x1600 portrait version:
the astronaut, planet and moon on top and, below it, the cleared panel and its mirror image as
a card for the readouts.

    .venv\Scripts\python.exe tools\prep_astronaut.py
"""
import random
from pathlib import Path

import pygame

from poster import clean, compose, letterbox, resurface

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_02_astronaut.png"
FACE = ROOT / "assets" / "faces" / "astronaut"
MATTE = (8, 9, 10)
PAPER = ((400, 340, 580, 470), (390, 480, 470, 590), (545, 30, 680, 125))   # clean cream paper


def is_paper(r, g, b):
    return r > 215 and g > 180 and b > 125


def is_night(r, g, b):
    return r < 40 and g < 60 and b < 85


def is_suit(r, g, b):
    """Her red shoulder and its dark maroon outline (the lettering is blue-black)."""
    return r - g > 55


PATCHES = (
    ((60, 40, 670, 345), None),                 # date and time
    ((66, 352, 440, 842), None),                # sun, temperature, CLEAR ... wind, WIND
    ((440, 730, 463, 812), is_suit),            # the end of SW, against her shoulder
)


def weave(poster, rect, sources, block=48, step=32, feather=10, seed=7):
    """Lay soft-edged tiles of `sources` over `rect`, so the edges of resurface()'s blocks melt."""
    rng = random.Random(seed)
    mask = pygame.Surface((block, block), pygame.SRCALPHA)
    for y in range(block):
        for x in range(block):
            edge = min(x, y, block - 1 - x, block - 1 - y)
            mask.set_at((x, y), (255, 255, 255, min(255, 255 * edge // feather)))
    sources = [pygame.Rect(s[0], s[1], s[2] - s[0], s[3] - s[1]) for s in sources]
    x0, y0, x1, y1 = rect
    clip = poster.get_clip()
    poster.set_clip(pygame.Rect(x0, y0, x1 - x0, y1 - y0))
    for y in range(y0 - block // 2, y1, step):
        for x in range(x0 - block // 2, x1, step):
            src = rng.choice(sources)
            sx = rng.randrange(src.left, src.right - block)
            sy = rng.randrange(src.top, src.bottom - block)
            tile = pygame.Surface((block, block), pygame.SRCALPHA)
            tile.blit(poster.subsurface((sx, sy, block, block)), (0, 0))
            tile = pygame.transform.flip(tile, rng.random() < 0.5, rng.random() < 0.5)
            tile.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            poster.blit(tile, (x + rng.randrange(-4, 5), y + rng.randrange(-4, 5)))
    poster.set_clip(clip)


def tone_match(poster, guide, rect, fine=8, broad=20):
    """Even out the new paper: take away its own light and shade (blurred over `fine` pixels),
    which hides tiles that came from lighter or darker spots, and put back the guide's (blurred
    over `broad`): the panel with the lettering painted out, which keeps the real shading of the
    paper but, close up, ghosts of the letters."""
    r = pygame.Rect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])

    def blur(surf, cell):
        small = (max(r.w // cell, 1), max(r.h // cell, 1))
        return pygame.transform.smoothscale(pygame.transform.smoothscale(surf.subsurface(r), small), r.size)

    want, have = blur(guide, broad), blur(poster, fine)
    lighter, darker = want.copy(), have.copy()
    lighter.blit(have, (0, 0), special_flags=pygame.BLEND_RGB_SUB)     # where the guide is lighter
    darker.blit(want, (0, 0), special_flags=pygame.BLEND_RGB_SUB)      # where it is darker
    poster.blit(lighter, r, special_flags=pygame.BLEND_RGB_ADD)
    poster.blit(darker, r, special_flags=pygame.BLEND_RGB_SUB)


def restore(poster, original, rect, keep):
    """Put back the original pixels of `rect` that pass keep(r, g, b)."""
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = original.get_at((x, y))
            if keep(c.r, c.g, c.b):
                poster.set_at((x, y), c)


if __name__ == "__main__":
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (2000, round(h * 2000 / w)))
    guide = clean(poster, [(rect, is_paper) for rect, _ in PATCHES])
    cleaned = guide.copy()
    for i, (rect, keep) in enumerate(PATCHES):
        resurface(cleaned, rect, PAPER, seed=5 + i)
        weave(cleaned, rect, PAPER, seed=7 + i)
        tone_match(cleaned, guide, rect)
        if keep:
            restore(cleaned, poster, rect, keep)
    letterbox(cleaned, FACE / "background.png", MATTE)
    art = clean(cleaned, [((1690, 40, 1724, 270), is_night)])    # the slogan's first letters, at the
    compose(art, FACE / "portrait.png", matte=MATTE, pieces=(
        ((745, 22, 975, 826), (0, 0, 720, 610)),     # edge of the astronaut, planet, moon and city
        ((10, 0, 316, 870), (0, 610, 360, 990)),
        ((10, 0, 316, 870), (360, 610, 360, 990), "mirror"),
    ))
