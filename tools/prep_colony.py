r"""Turn the robot-colony mockup into the colony face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons, values and labels: the face
draws all of them live) and letterboxes to 1600x720, keeping the slogan. Behind the readouts
lies a red sky gradient and, lower down, dark canyon rock, so the lettering (and its soft dark
halo) is not covered with copied blocks but inpainted: the holes are filled with a smooth
estimate of the surrounding picture, with the fine detail of clean stretches nearby (rock
texture, grain, stars) laid over it.

The 720x1600 portrait version puts the robot, the planet and the colony's towers on top and,
below them, the cleared column and its mirror image as a card for the readouts.

    .venv\Scripts\python.exe tools\prep_colony.py
"""
import random
from pathlib import Path

import pygame

from poster import compose, letterbox

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_04_robot_colony.png"
FACE = ROOT / "assets" / "faces" / "colony"
MATTE = (9, 7, 8)
WIDTH = 2000


def is_ink(r, g, b):
    """The cream lettering and icons and the amber sun, not the red sky or orange rock."""
    return r > 140 and g > 100 and (b > 110 or g > 140)


def inpaint(poster, rect, wanted, grow, cell=8, tile=24, reach=200, seed=7):
    """Fill the pixels of `rect` (x0, y0, x1, y1) that pass wanted(r, g, b), and everything within
    `grow` px of them (their halo), from the clean picture around them: a smooth surface that
    joins the hole's edges, with the fine detail of clean stretches nearby laid over it."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    sub = poster.subsurface((x0, y0, w, h))
    px = bytearray(pygame.image.tobytes(sub, "RGB"))
    ink = pygame.mask.Mask((w, h))
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            if wanted(px[i], px[i + 1], px[i + 2]):
                ink.set_at((x, y))
    disk = pygame.mask.Mask((grow * 2 + 1, grow * 2 + 1))
    for dy in range(-grow, grow + 1):
        for dx in range(-grow, grow + 1):
            if dx * dx + dy * dy <= grow * grow + grow:
                disk.set_at((dx + grow, dy + grow))
    hole = ink.convolve(disk, pygame.mask.Mask((w, h)), (-grow, -grow))

    # The smooth estimate: mean colour of the clean pixels in each cell, cells that are mostly
    # hole relaxed to the average of their neighbours until the surface settles.
    gw, gh = -(-w // cell), -(-h // cell)
    grid, fixed = [[None] * gw for _ in range(gh)], [[False] * gw for _ in range(gh)]
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
                grid[cy][cx], fixed[cy][cx] = [v / n for v in s], True
    free = [(cx, cy) for cy in range(gh) for cx in range(gw) if not fixed[cy][cx]]
    while any(grid[cy][cx] is None for cx, cy in free):     # first, grow in from the edges
        for cx, cy in free:
            if grid[cy][cx] is None:
                near = [grid[y][x] for x, y in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1))
                        if 0 <= x < gw and 0 <= y < gh and grid[y][x] is not None]
                if near:
                    grid[cy][cx] = [sum(c) / len(near) for c in zip(*near)]
    for _ in range(300):                                     # then relax
        for cx, cy in free:
            near = [grid[y][x] for x, y in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1))
                    if 0 <= x < gw and 0 <= y < gh]
            grid[cy][cx] = [sum(c) / len(near) for c in zip(*near)]

    def smooth(x, y):
        fx, fy = min(max((x + 0.5) / cell - 0.5, 0), gw - 1), min(max((y + 0.5) / cell - 0.5, 0), gh - 1)
        ix, iy = min(int(fx), gw - 2), min(int(fy), gh - 2)
        ax, ay = fx - ix, fy - iy
        a, b, c, d = grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix], grid[iy + 1][ix + 1]
        return [(a[k] * (1 - ax) + b[k] * ax) * (1 - ay) + (c[k] * (1 - ax) + d[k] * ax) * ay for k in range(3)]

    # The grain: each tile of the hole borrows the fine detail (picture minus smooth surface)
    # of a clean stretch of the same size nearby, as close to its own height as there is. Tiles
    # deep inside a big hole wait for their neighbours to be filled and borrow from those.
    rng, out, filled = random.Random(seed), bytearray(px), 0
    original, holes, shift = bytes(px), hole.copy(), {}
    shifts = sorted(((dx, dy) for dx in range(-reach, reach + 1, 4) for dy in range(-64, 65, 4)),
                    key=lambda d: (abs(d[1]) // 12, rng.random()))
    pending = [(tx, ty) for ty in range(0, h, tile) for tx in range(0, w, tile)]
    while pending:
        done, waiting = [], []
        for tx, ty in pending:
            part = pygame.mask.Mask((tile, tile))
            part.draw(hole, (-tx, -ty))
            if not part.count():
                continue
            box = part.get_bounding_rects()
            box = box[0].unionall(box[1:])
            for dx, dy in shifts:
                left, top = tx + box.left + dx, ty + box.top + dy
                if (0 <= left and left + box.width <= w and 0 <= top and top + box.height <= h
                        and not hole.overlap_area(part, (tx + dx, ty + dy))):
                    break
            else:
                waiting.append((tx, ty))
                continue
            for y in range(ty + box.top, ty + box.bottom):
                for x in range(tx + box.left, tx + box.right):
                    if part.get_at((x - tx, y - ty)):
                        base, near = smooth(x, y), smooth(x + dx, y + dy)
                        i, j = (y * w + x) * 3, ((y + dy) * w + x + dx) * 3
                        for k in range(3):
                            out[i + k] = max(0, min(255, round(base[k] + px[j + k] - near[k])))
                        filled += 1
            done.append((part, tx, ty))
            shift[tx, ty] = dx, dy
        if not done:
            raise SystemExit(f"no clean stretch for the tiles at {[(x + x0, y + y0) for x, y in waiting]}")
        for part, tx, ty in done:
            hole.erase(part, (tx, ty))
        px[:] = out
        pending = waiting

    # Then the tiles' seams are feathered: near a tile's edge its detail is mixed with that of
    # its neighbours' sources, from the filled picture.
    px, out, band = bytes(out), bytearray(original), tile // 3

    def ramp(d):
        return min(max((d + band) / (2 * band), 0.0), 1.0)

    for y in range(h):
        for x in range(w):
            if not holes.get_at((x, y)):
                continue
            mix, total = [0.0, 0.0, 0.0], 0.0
            for ty in range((y - band) // tile * tile, (y + band) // tile * tile + 1, tile):
                for tx in range((x - band) // tile * tile, (x + band) // tile * tile + 1, tile):
                    if (tx, ty) not in shift:
                        continue
                    dx, dy = shift[tx, ty]
                    sx, sy = min(max(x + dx, 0), w - 1), min(max(y + dy, 0), h - 1)
                    k = ramp(x - tx) * ramp(tx + tile - x) * ramp(y - ty) * ramp(ty + tile - y)
                    if k > 0:
                        near, j = smooth(sx, sy), (sy * w + sx) * 3
                        for c in range(3):
                            mix[c] += k * (px[j + c] - near[c])
                        total += k
            base, i = smooth(x, y), (y * w + x) * 3
            for c in range(3):
                out[i + c] = max(0, min(255, round(base[c] + mix[c] / max(total, 1e-6))))
    poster.blit(pygame.image.frombytes(bytes(out), (w, h), "RGB"), (x0, y0))
    print(f"inpainted {filled} px in {rect}")


if __name__ == "__main__":
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    cleaned = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    inpaint(cleaned, (62, 36, 620, 300), is_ink, grow=9)        # date and time, on the sky
    inpaint(cleaned, (60, 300, 431, 800), is_ink, grow=8)       # the weather column, on the
    inpaint(cleaned, (431, 680, 560, 780), is_ink, grow=8)      # darkened sky and rock, and
    letterbox(cleaned, FACE / "background.png", MATTE)           # the W poking out of it
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        ((552, 18, 860, 812), (0, 0, 720, 680)),                 # the robot, planet and towers
        ((10, 0, 415, 846), (0, 680, 360, 920)),                 # the cleared column ...
        ((10, 0, 415, 846), (360, 680, 360, 920), "mirror"),     # ... and its mirror image
    ))
