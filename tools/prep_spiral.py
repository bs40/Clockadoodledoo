r"""Turn the flower-spiral mockup into the spiral face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all
of them live) and letterboxes to 1600x720. Behind the readouts lies a dark, out-of-focus starry
background with soft bokeh and no fine texture worth copying (blocks of copied texture would
show), so the lettering and its broad dark halo are misted over (mist()): a smooth surface
stretched between the clean picture around them, with a faint even grain, its edges melted
into the picture.

The 720x1600 portrait version puts the spiral of flowers and its golden centre on top and,
below it, the cleared column and its mirror image as a dark bokeh card for the readouts, the
art fading softly into the card.

The mockup on hand is small (755x332) and is scaled up to 2000 px wide here, so the result is
soft. Every position is in those 2000-wide pixels, so a full-size copy of the poster can be
dropped in later by changing SRC alone (and POSTER_H in clock/faces/spiral.py if its height at
2000 wide differs from 879).

    .venv\Scripts\python.exe tools\prep_spiral.py
"""
import random
from pathlib import Path

import pygame

from poster import PORTRAIT, letterbox

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "Psychedelic_Clock_06.png"
FACE = ROOT / "assets" / "faces" / "spiral"
MATTE = (7, 8, 11)
WIDTH = 2000

ART = (804, 12, 697, 852)            # portrait: the spiral and its golden centre (poster x, y, w, h)
TOP, FADE = 880, 150                 # the art's height on the portrait, and its fade into the card
COLUMN = (30, 60, 280, 740)          # portrait: the cleared dark column, mirrored beside itself


def is_ink(r, g, b):
    """The cream time and the peach date, icons and values, not the dark bokeh behind them."""
    return r > 120 and g > 85 and r - b > 45 and g > r * 0.55


def _disk(r):
    disk = pygame.mask.Mask((r * 2 + 1, r * 2 + 1))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                disk.set_at((dx + r, dy + r))
    return disk


def mist(poster, area, finds, wanted, grow, cell=8, grain=1.6, soft=10, seed=7):
    """Paint out lettering on soft, out-of-focus background: the pixels in the `finds` rects that
    pass wanted(r, g, b), and everything within `grow` px of them (the lettering's soft dark
    halo), become a smooth surface stretched between the clean picture around them (a membrane
    over a grid of `cell` px, relaxed until it settles), with a faint even grain. The filled
    pixels then melt into their surroundings over `soft` px, so no edge shows. All rects are
    (x0, y0, x1, y1) in poster pixels; `area`, which holds the finds with room to spare, is
    the picture the membrane is stretched in."""
    ax, ay, ax1, ay1 = area
    w, h = ax1 - ax, ay1 - ay
    sub = poster.subsurface((ax, ay, w, h))
    px = pygame.image.tobytes(sub, "RGB")
    ink = pygame.mask.Mask((w, h))
    for x0, y0, x1, y1 in finds:
        for y in range(y0 - ay, y1 - ay):
            for x in range(x0 - ax, x1 - ax):
                i = (y * w + x) * 3
                if wanted(px[i], px[i + 1], px[i + 2]):
                    ink.set_at((x, y))
    hole = ink.convolve(_disk(grow), pygame.mask.Mask((w, h)), (-grow, -grow))

    # The membrane: each cell that is mostly clean holds the mean of its clean pixels; the rest
    # grow in from their neighbours, then relax (over-relaxed Gauss-Seidel) until smooth.
    gw, gh = -(-w // cell), -(-h // cell)
    grid, free = [[None] * gw for _ in range(gh)], []
    for cy in range(gh):
        for cx in range(gw):
            s, n, total = [0, 0, 0], 0, 0
            for y in range(cy * cell, min(cy * cell + cell, h)):
                for x in range(cx * cell, min(cx * cell + cell, w)):
                    total += 1
                    if not hole.get_at((x, y)):
                        i = (y * w + x) * 3
                        s[0] += px[i]; s[1] += px[i + 1]; s[2] += px[i + 2]; n += 1
            if n * 2 >= total:
                grid[cy][cx] = [v / n for v in s]
            else:
                free.append((cx, cy))

    def near(cx, cy):
        return [grid[y][x] for x, y in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1))
                if 0 <= x < gw and 0 <= y < gh and grid[y][x] is not None]

    while any(grid[cy][cx] is None for cx, cy in free):
        for cx, cy in free:
            if grid[cy][cx] is None and near(cx, cy):
                grid[cy][cx] = [sum(c) / len(near(cx, cy)) for c in zip(*near(cx, cy))]
    for _ in range(500):
        for cx, cy in free:
            nb = near(cx, cy)
            old = grid[cy][cx]
            grid[cy][cx] = [o + 1.8 * (sum(c) / len(nb) - o) for o, c in zip(old, zip(*nb))]

    def smooth(x, y):
        fx, fy = min(max((x + 0.5) / cell - 0.5, 0), gw - 1), min(max((y + 0.5) / cell - 0.5, 0), gh - 1)
        ix, iy = min(int(fx), gw - 2), min(int(fy), gh - 2)
        kx, ky = fx - ix, fy - iy
        a, b, c, d = grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix], grid[iy + 1][ix + 1]
        return [(a[k] * (1 - kx) + b[k] * kx) * (1 - ky) + (c[k] * (1 - kx) + d[k] * kx) * ky for k in range(3)]

    rng, out = random.Random(seed), bytearray(px)
    for y in range(h):
        for x in range(w):
            if hole.get_at((x, y)):
                base, n, i = smooth(x, y), rng.gauss(0, grain), (y * w + x) * 3
                for k in range(3):
                    out[i + k] = max(0, min(255, round(base[k] + n)))
    filled = pygame.image.frombytes(bytes(out), (w, h), "RGB")

    # Melt the edges: a blurred copy of the filled picture is laid over the hole and a soft
    # band around it (the band's own detail kept a little, the hole's grain kept).
    mask = hole.convolve(_disk(soft // 2), pygame.mask.Mask((w, h)), (-(soft // 2), -(soft // 2)))
    weight = mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0))
    small = (max(w // soft, 1), max(h // soft, 1))
    weight = pygame.transform.smoothscale(pygame.transform.smoothscale(weight, small), (w, h))
    small = (max(w // 4, 1), max(h // 4, 1))
    blur = pygame.transform.smoothscale(pygame.transform.smoothscale(filled, small), (w, h))
    fb, bb, wb = (pygame.image.tobytes(s, "RGB") for s in (filled, blur, weight))
    out = bytearray(fb)
    for p in range(w * h):
        k = wb[p * 3] / 255
        if k <= 0:
            continue
        if hole.get_at((p % w, p // w)):
            k = 0.6                                     # in the hole: mostly the grain kept
        for c in range(3):
            j = p * 3 + c
            out[j] = round(fb[j] + (bb[j] - fb[j]) * k * 0.8)
    poster.blit(pygame.image.frombytes(bytes(out), (w, h), "RGB"), (ax, ay))
    print(f"misted {hole.count()} px in {area}")


def build():
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    mist(poster, (40, 16, 700, 836), (
        (66, 30, 632, 222),             # the time
        (84, 228, 598, 310),            # the date
        (62, 336, 380, 792),            # icons and values
    ), is_ink, grow=22, soft=16)
    letterbox(poster, FACE / "background.png", MATTE)
    return poster


def portrait(cleaned, out):
    canvas = pygame.Surface(PORTRAIT)
    canvas.fill(MATTE)
    card_h = PORTRAIT[1] - TOP + FADE
    card = pygame.transform.smoothscale(cleaned.subsurface(COLUMN), (360, card_h))
    canvas.blit(card, (0, TOP - FADE))
    canvas.blit(pygame.transform.flip(card, True, False), (360, TOP - FADE))
    art = pygame.transform.smoothscale(cleaned.subsurface(ART), (PORTRAIT[0], TOP)).convert_alpha()
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
