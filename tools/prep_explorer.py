r"""Turn the distant-world mockup into the explorer face's backgrounds (landscape and portrait).

Covers the baked-in date, time and the weather column (icons, values and labels: the face
draws all of them live) and keeps the slogan. The sky there is a teal gradient that brightens
towards the horizon and towards the moon, so it is repainted row by row as a blend of the sky
either side, with grain and stars from clean sky at the same height (sky()); the wind row lies
over the far ridge and streaky rock, and its lettering is blended out along the rows
(unletter()). Letterboxes to 1600x720 and composes a 720x1600 portrait version: the astronaut
on top and, below him, the cleared sky and its mirror image as a card for the readouts.

    .venv\Scripts\python.exe tools\prep_explorer.py
"""
import random
import statistics
from pathlib import Path

import pygame

from poster import compose, letterbox

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_06_distant_world.png"
FACE = ROOT / "assets" / "faces" / "explorer"
MATTE = (8, 9, 10)

CLEAR_SKY = (                         # clean sky to take grain and stars from
    (1676, 40, 1758, 102), (1714, 96, 1758, 276),      # between the date, time and slogan
    (1560, 268, 1760, 445),                            # right of the rows, before the plane's tail
    (1598, 425, 1640, 470), (1188, 425, 1256, 500),    # either side of the pressure row
)


# where the face writes small text: a star there would read as a stray full stop
TEXT_LINES = ((1250, 50, 1712, 100),                                         # the date
              (1385, 285, 1606, 360), (1385, 362, 1606, 434), (1385, 444, 1606, 524), (1385, 534, 1606, 612))


def is_sky(c):
    """Teal or the pale haze above the horizon, not the red rock."""
    return c[1] > c[0] * 0.85


def is_haze(c):
    """Sky, strictly: the haze low down is grey; dusty rock just below it is a touch redder."""
    return c[1] > c[0] * 0.92


def is_lettering(r, g, b):
    """The cream lettering (the haze over the ridge is greyer and darker, the rock redder)."""
    return r > 180 and g > 165 and b > 125


def beside_plane(x, y):
    """On or below the rim of the spaceplane's canopy, which runs up to the right past the wind."""
    return x >= 1578 or y >= 600 - (x - 1540) * 0.57 - 8


def _pixels(surf):
    return bytearray(pygame.image.tobytes(surf, "RGB"))


def _blur(surf, k):
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(w // k, 1), max(h // k, 1)))
    return _pixels(pygame.transform.smoothscale(small, (w, h)))


def _edge(poster, x0, x1, y0, y1, until=None):
    """Median sky colour of the columns x0..x1 on each row y0..y1, smoothed down the rows; rows
    where the strip is not sky, or below `until`, take the nearest good row's colour."""
    rows = []
    for y in range(y0, y1):
        px = [poster.get_at((x, y)) for x in range(x0, x1)]
        rows.append(tuple(statistics.median(p[i] for p in px) for i in range(3)))
    good = [i for i, c in enumerate(rows) if is_sky(c) and (until is None or y0 + i < until)]
    rows = [rows[min(good, key=lambda g: abs(g - i))] for i in range(len(rows))]
    out = []
    for i in range(len(rows)):
        window = rows[max(i - 10, 0):i + 11]
        out.append(tuple(sum(c[k] for c in window) / len(window) for k in range(3)))
    return out


def _grain(poster, size, sources, rng, block=32):
    """Print grain for a patch `size`: blocks of the fine detail of clean sky in `sources` (the
    sky less its broad shading). Stars are left out, so they don't repeat; they come back as
    stamps cut from the sources (returned with how many there are per pixel)."""
    w, h = size
    fine, stamps, area = [], [], 0
    for s in sources:
        rect = pygame.Rect(s[0], s[1], s[2] - s[0], s[3] - s[1])
        px, bl, sw = _pixels(poster.subsurface(rect)), _blur(poster.subsurface(rect), 12), rect.width
        d = [px[i] - bl[i] for i in range(len(px))]
        lum = [d[i] + d[i + 1] + d[i + 2] for i in range(0, len(d), 3)]
        for y in range(rect.height):
            for x in range(sw):
                v = lum[y * sw + x]
                if v > 60 and 2 <= x < sw - 2 and 2 <= y < rect.height - 2 and                         all(v >= lum[(y + dy) * sw + x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                    stamps.append([[max(d[((y + dy) * sw + x + dx) * 3 + c], 0) for c in range(3)]
                                   for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)])
        star = [v > 24 for v in lum]                      # stars (and the dip around them) out
        for i, on in enumerate(star):
            x, y = i % sw, i // sw
            if on or any(star[yy * sw + xx] for yy in range(max(y - 3, 0), min(y + 4, rect.height))
                         for xx in range(max(x - 3, 0), min(x + 4, sw))):
                d[i * 3:i * 3 + 3] = (0, 0, 0)
            else:
                d[i * 3:i * 3 + 3] = [max(min(v, 12), -12) for v in d[i * 3:i * 3 + 3]]
        fine.append((rect, d))
        area += rect.width * rect.height
    grain = [0] * (w * h * 3)
    bh = block // 2
    for y in range(0, h, bh):
        for x in range(0, w, block):
            rect, d = rng.choices(fine, [r.width * r.height for r, _ in fine])[0]
            sx = rng.randrange(0, max(rect.width - block, 1))
            sy = rng.randrange(0, max(rect.height - bh, 1))
            flip = rng.random() < 0.5
            for yy in range(min(bh, h - y)):
                for xx in range(min(block, w - x)):
                    j = ((sy + yy) * rect.width + sx + (block - 1 - xx if flip else xx)) * 3
                    i = ((y + yy) * w + x + xx) * 3
                    grain[i:i + 3] = d[j:j + 3]
    return grain, stamps, len(stamps) / area


def sky(poster, rect, sources=CLEAR_SKY, seed=7, horizon=None, until=(None, None), bare=TEXT_LINES):
    """Repaint `rect` (x0, y0, x1, y1) as sky: on each row, a blend from the sky just left of it
    to the sky just right of it, with the print grain and a scatter of stars from `sources`
    (fewer down in the haze, none in the `bare` rects). With `horizon` (a row), each column stops
    where the rock begins below that row; `until` gives the rows below which the sky either side
    is hidden by rock (left, right)."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    tops = [h] * w
    if horizon:
        for x in range(w):
            for y in range(horizon - y0, h - 2):
                if not any(is_haze(poster.get_at((x0 + x, y0 + y + k))) for k in range(3)):
                    tops[x] = y
                    break
    left = _edge(poster, x0 - 12, x0 - 2, y0, y1, until[0])
    right = _edge(poster, x1 + 2, x1 + 12, y0, y1, until[1])
    grain, stamps, density = _grain(poster, (w, h), sources, rng)
    out = bytearray(w * h * 3)
    for y in range(h):
        lc, rc = left[y], right[y]
        for x in range(w):
            k, i = x / (w - 1), (y * w + x) * 3
            for c in range(3):
                out[i + c] = max(min(int(lc[c] + (rc[c] - lc[c]) * k) + grain[i + c], 255), 0)
    count = round(density * w * h)
    for _ in range(count):
        cx, cy, stamp = rng.randrange(2, w - 2), rng.randrange(2, h - 2), rng.choice(stamps)
        if rng.random() > (360 - sum(out[(cy * w + cx) * 3:(cy * w + cx) * 3 + 3])) / 100:
            continue                                      # few stars low in the haze
        if any(pygame.Rect(b[0], b[1], b[2] - b[0], b[3] - b[1]).collidepoint(x0 + cx, y0 + cy) for b in bare):
            continue
        for j in range(25):
            i = ((cy + j // 5 - 2) * w + cx + j % 5 - 2) * 3
            for c in range(3):
                out[i + c] = min(out[i + c] + stamp[j][c], 255)
    patch = pygame.image.frombytes(bytes(out), (w, h), "RGB")
    for x in range(w):
        poster.blit(patch, (x0 + x, y0), (x, 0, 1, tops[x]))
    print(f"sky {rect}: {count} stars")


def unletter(poster, rect, is_letter, skip=lambda x, y: False, grow=5):
    """Take lettering off scenery laid out in level bands (a far ridge, streaky rock): each
    lettered stretch of a row becomes a blend from the row's clean pixels just left of it to
    those just right of it, with grain borrowed from beside it."""
    x0, y0, x1, y1 = rect
    pad = 24
    area = pygame.Rect(x0 - pad, y0, x1 - x0 + pad * 2, y1 - y0)
    px, bl = _pixels(poster.subsurface(area)), _blur(poster.subsurface(area), 6)
    aw, h = area.size
    hit = [[0] * aw for _ in range(h)]
    for y in range(h):
        for x in range(pad, aw - pad):
            i = (y * aw + x) * 3
            if is_letter(px[i], px[i + 1], px[i + 2]) and not skip(area.x + x, y0 + y):
                for yy in range(max(y - grow, 0), min(y + grow + 1, h)):
                    for xx in range(x - grow, x + grow + 1):
                        if not skip(area.x + xx, y0 + yy):
                            hit[yy][xx] = 1

    def side(y, xs):                                   # median colour of nearby clean pixels
        vals = [px[(yy * aw + x) * 3:(yy * aw + x) * 3 + 3] for yy in (y - 1, y, y + 1) if 0 <= yy < h
                for x in xs if 0 <= x < aw and not hit[yy][x]]
        return [statistics.median(v[c] for v in vals) for c in range(3)] if vals else None

    out, filled = bytearray(px), 0
    for y in range(h):
        x = 0
        while x < aw:
            if not hit[y][x]:
                x += 1
                continue
            a = x
            while x < aw and hit[y][x]:
                x += 1
            b, n = x, x - a                            # the run a .. b-1
            lc = side(y, range(a - 8, a)) or side(y, range(b, b + 8))
            rc = side(y, range(b, b + 8)) or lc
            for j in range(n):
                k = (j + 1) / (n + 1)
                g = min(max(a - n - 3 + j if a - n - 3 >= 0 else b + 3 + j, 0), aw - 1)
                gi, i = (y * aw + g) * 3, (y * aw + a + j) * 3
                for c in range(3):
                    grain = 0 if hit[y][g] else max(min(px[gi + c] - bl[gi + c], 16), -16)
                    v = lc[c] + (rc[c] - lc[c]) * k + grain
                    out[i + c] = max(min(int(v), 255), 0)
            filled += n
    poster.blit(pygame.image.frombytes(bytes(out), area.size, "RGB"), area.topleft)
    print(f"unlettered {filled} px in {rect}")


def build():
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (2000, round(h * 2000 / w)))
    unletter(poster, (1250, 530, 1600, 616), is_lettering, beside_plane)    # the wind row
    sky(poster, (1248, 44, 1712, 272))                  # date and time
    sky(poster, (1248, 272, 1606, 432), seed=8)         # temperature and humidity
    sky(poster, (1248, 432, 1606, 582), seed=9, horizon=535, until=(538, 512))    # pressure, wind
    letterbox(poster, FACE / "background.png", MATTE)
    return poster


if __name__ == "__main__":
    cleaned = build()
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        ((20, 16, 886, 838), (0, 0, 720, 681)),                         # the astronaut and the crescent
        ((1240, 24, 300, 570), (0, 681, 360, 919)),                     # cleared sky down to the ridge
        ((1240, 24, 300, 570), (360, 681, 360, 919), "mirror"),
    ))
