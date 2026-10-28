r"""Turn the orbital-station mockup into the station face's backgrounds (landscape and portrait).

Covers the baked-in date, time, temperature row (sun, value and CLEAR) and the three values of
the top-right table (its labels stay: the face draws the values live), letterboxes to 1600x720,
and composes a 720x1600 portrait version: the ship above the station and, below them, plain
starry sky for the readouts (made up to match: blocks of the poster's own sky showed as a
patchwork) with the VISIBLE TONIGHT panel set into it. The station, the sky and the panel
fade in at their edges (overlay), so no seams show.

The date and time lie partly over the planet's banded shadow side, so they are not covered with
copied blocks but filled in along the bands (streak_fill): each covered pixel takes the colours
found where its band leaves the lettering, on either side.

    .venv\Scripts\python.exe tools\prep_station.py
"""
import random
from pathlib import Path

import pygame

from poster import compose, letterbox

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_05_orbital_station.png"
FACE = ROOT / "assets" / "faces" / "station"
MATTE = (6, 9, 16)
BANDS = 33                  # the planet's bands run down to the right at about this angle (degrees)
HALO = 10                   # the lettering's dark halo, in poster pixels
SHIP = ((45, 452, 860, 286), (0, 0, 720, 239))             # portrait pieces, (x, y, w, h): the
STATION = ((960, 178, 660, 622), (0, 239, 720, 679))       # face maps its effects with these
CARD = ((0, 60, 720, 682), (0, 918, 720, 682))             # (from starry_sky(), not the poster)
PANEL = ((1665, 428, 272, 320), (432, 1270, 272, 320))


def is_cream(r, g, b):
    """The cream lettering (not the planet's orange, whose blue is far lower)."""
    return r > 110 and g > 100 and b > 75 and r - b < 80


def is_lit(r, g, b):
    """Anything brighter than the night sky: the sun icon."""
    return r > 60 or g > 60


def streak_fill(poster, jobs, angle=BANDS, grow=HALO, margin=60, seed=7):
    """Paint out lettering by carrying the background in along the planet's bands. jobs:
    ((x0, y0, x1, y1), is_ink(r, g, b)); the ink, grown by `grow` pixels to take its halo, is
    replaced, in a frame turned so that the bands run level, by a blend of the colours where
    each row leaves the ink on the left and on the right, with a little grain."""
    w, h = poster.get_size()
    x0 = max(min(r[0] for r, _ in jobs) - margin, 0)
    y0 = max(min(r[1] for r, _ in jobs) - margin, 0)
    x1 = min(max(r[2] for r, _ in jobs) + margin, w)
    y1 = min(max(r[3] for r, _ in jobs) + margin, h)
    area = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
    ink = pygame.mask.Mask(area.size)
    for (a, b, c, d), is_ink in jobs:
        for y in range(b, d):
            for x in range(a, c):
                if is_ink(*poster.get_at((x, y))[:3]):
                    ink.set_at((x - x0, y - y0))
    disc = pygame.mask.Mask((2 * grow + 1, 2 * grow + 1))
    for y in range(2 * grow + 1):
        for x in range(2 * grow + 1):
            if (x - grow) ** 2 + (y - grow) ** 2 <= grow * grow:
                disc.set_at((x, y))
    hole = pygame.mask.Mask(area.size)
    for x, y in _set_bits(ink):
        hole.draw(disc, (x - grow, y - grow))

    # Turn the picture and the hole so that the bands run level.
    sub = poster.subsurface(area).copy().convert_alpha()
    flags = hole.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255)).convert_alpha()
    rot = pygame.transform.rotozoom(sub, angle, 1)
    rflags = pygame.transform.rotozoom(flags, angle, 1)
    rw, rh = rot.get_size()
    rng = random.Random(seed)

    def sample(row, x, step):
        """Middle colour of a few clean pixels just beyond the edge of the hole (a stray star
        among them doesn't count), or None."""
        got = []
        for k in range(2, 10):
            xx = x + step * k
            if 0 <= xx < rw:
                f = rflags.get_at((xx, row))
                if f.a > 250 and f.r < 5:
                    got.append(rot.get_at((xx, row)))
        if not got:
            return None
        return [sorted(c[i] for c in got)[len(got) // 2] for i in range(3)]

    for row in range(rh):
        x = 0
        while x < rw:
            f = rflags.get_at((x, row))
            if not (f.a > 128 and f.r > 128):
                x += 1
                continue
            start = x
            while x < rw and rflags.get_at((x, row)).r > 128 and rflags.get_at((x, row)).a > 128:
                x += 1
            left, right = sample(row, start - 1, -1), sample(row, x, 1)
            if left is None and right is None:
                continue
            left, right = left or right, right or left
            n = x - start + 1
            for i in range(start, x):
                k = (i - start + 1) / n
                grain = rng.gauss(0, 2.5)
                rot.set_at((i, row), [max(0, min(255, int(left[c] + (right[c] - left[c]) * k + grain))) for c in range(3)])

    back = pygame.transform.rotozoom(rot, -angle, 1)
    bx, by = (back.get_width() - area.width) // 2, (back.get_height() - area.height) // 2
    for x, y in _set_bits(hole):
        poster.set_at((x0 + x, y0 + y), back.get_at((bx + x, by + y)))
    print(f"streak-filled {hole.count()} px in {tuple(area)}")


def overlay(canvas, poster, src, dst, fade, edges="tlrb"):
    """Place a piece like compose() does, but fading in over `fade` canvas pixels along the
    given edges (top, left, right, bottom), and on the top edge reaching `fade` pixels higher
    up than dst so that the fade covers the piece below's last rows."""
    k = dst[2] / src[2]
    if "t" in edges:
        grow = round(fade / k)
        src = (src[0], src[1] - grow, src[2], src[3] + grow)
        dst = (dst[0], dst[1] - fade, dst[2], dst[3] + fade)
    piece = pygame.transform.smoothscale(poster.subsurface(pygame.Rect(src)), dst[2:]).convert_alpha()
    w, h = dst[2:]
    alpha = pygame.Surface((w, h), pygame.SRCALPHA)
    alpha.fill((255, 255, 255, 255))
    for i in range(fade):                 # rings from the edge inwards, each a little stronger
        a = (255, 255, 255, int(255 * (i + 0.5) / fade))
        if "t" in edges:
            pygame.draw.line(alpha, a, (i if "l" in edges else 0, i), (w - 1 - (i if "r" in edges else 0), i))
        if "b" in edges:
            pygame.draw.line(alpha, a, (i if "l" in edges else 0, h - 1 - i), (w - 1 - (i if "r" in edges else 0), h - 1 - i))
        if "l" in edges:
            pygame.draw.line(alpha, a, (i, i if "t" in edges else 0), (i, h - 1 - (i if "b" in edges else 0)))
        if "r" in edges:
            pygame.draw.line(alpha, a, (w - 1 - i, i if "t" in edges else 0), (w - 1 - i, h - 1 - (i if "b" in edges else 0)))
    piece.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    canvas.blit(piece, dst[:2])


def starry_sky(size, top, bottom, seed=8):
    """Plain night sky like the poster's: a gradient from `top` to `bottom` colour over the
    first third, faint mottling and grain, and a sprinkle of small stars."""
    w, h = size
    rng = random.Random(seed)
    sky = pygame.Surface(size)
    for y in range(h):
        k = min(y / (h / 3), 1.0) ** 0.8
        sky.fill([round(a + (b - a) * k) for a, b in zip(top, bottom)], (0, y, w, 1))
    for scale, depth in ((60, 7), (3, 4)):                 # mottling, then grain
        for flag in (pygame.BLEND_RGB_ADD, pygame.BLEND_RGB_SUB):
            noise = pygame.Surface((w // scale + 2, h // scale + 2))
            for y in range(noise.get_height()):
                for x in range(noise.get_width()):
                    v = rng.randrange(depth)
                    noise.set_at((x, y), (v, v, v + rng.randrange(2)))
            sky.blit(pygame.transform.smoothscale(noise, (w + 2 * scale, h + 2 * scale)), (-scale, -scale), special_flags=flag)
    for _ in range(w * h // 900):                          # stars: mostly faint specks
        x, y = rng.randrange(w), rng.randrange(h)
        base = sky.get_at((x, y))
        k = rng.choice((0.25, 0.3, 0.4, 0.5, 0.6, 0.8))
        star = rng.choice(((255, 240, 205), (220, 230, 255)))
        c = [round(b + (s - b) * k) for b, s in zip(base[:3], star)]
        sky.set_at((x, y), c)
        if k >= 0.5 and rng.random() < 0.5:                # brighter ones get a soft cross
            soft = [round(b + (s - b) * k * 0.4) for b, s in zip(base[:3], star)]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < w and 0 <= y + dy < h:
                    sky.set_at((x + dx, y + dy), soft)
    return sky


def _set_bits(mask):
    w, h = mask.get_size()
    return [(x, y) for y in range(h) for x in range(w) if mask.get_at((x, y))]


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    poster = pygame.image.load(str(SRC)).convert()
    w, h = poster.get_size()
    cleaned = pygame.transform.smoothscale(poster, (2000, round(h * 2000 / w)))
    streak_fill(cleaned, (
        ((90, 45, 565, 105), is_cream),            # date
        ((90, 108, 645, 305), is_cream),           # time
        ((95, 318, 212, 442), is_lit),             # sun
        ((245, 328, 400, 442), is_cream),          # 16°C and CLEAR
    ))
    streak_fill(cleaned, (((1752, 45, 1935, 228), is_cream),), angle=90)    # humidity, pressure and
                                                                           # wind values: from the sky
                                                                           # above and below each
    letterbox(cleaned, FACE / "background.png", MATTE)

    bare = cleaned.copy()                              # portrait: the table's labels go too (the
    streak_fill(bare, (((1565, 45, 1700, 228), is_cream),), angle=90)    # station piece reaches WIND)
    card = starry_sky((720, 742), (7, 36, 51), (3, 14, 27))    # and plain sky for the readouts
    compose(bare, FACE / "portrait.png", matte=MATTE, pieces=(SHIP, STATION))
    portrait = pygame.image.load(str(FACE / "portrait.png")).convert()
    overlay(portrait, bare, *STATION, fade=40, edges="t")
    overlay(portrait, card, *CARD, fade=40, edges="t")
    overlay(portrait, bare, *PANEL, fade=14)
    pygame.image.save(portrait, str(FACE / "portrait.png"))
    print("faded in the station, the sky and the panel")
