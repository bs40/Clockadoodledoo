"""Shared steps for turning a poster mockup into face backgrounds.

A mockup has example readouts baked into it. paint_out() removes them by copying nearby clean
background over them. prepare() does that for a list of regions and letterboxes the poster to
the landscape screen; compose() cuts pieces out of the cleaned poster and arranges them on a
portrait canvas.
"""
import random

import pygame

TARGET = (1600, 720)
PORTRAIT = (720, 1600)
GROW = 3  # widen the painted-out area to catch soft edges


def paint_out(px, w, h, rect, is_bg, rng):
    x0, y0, x1, y1 = rect
    rw, rh = x1 - x0, y1 - y0
    mask = bytearray(rw * rh)
    for y in range(rh):
        row = ((y0 + y) * w + x0) * 3
        for x in range(rw):
            i = row + x * 3
            if not is_bg(px[i], px[i + 1], px[i + 2]):
                mask[y * rw + x] = 1

    grown = bytearray(mask)
    for y in range(rh):
        for x in range(rw):
            if mask[y * rw + x]:
                for yy in range(max(y - GROW, 0), min(y + GROW + 1, rh)):
                    base = yy * rw
                    for xx in range(max(x - GROW, 0), min(x + GROW + 1, rw)):
                        grown[base + xx] = 1

    def clean(sx, sy):
        if not (0 <= sx < w and 0 <= sy < h):
            return False
        if x0 <= sx < x1 and y0 <= sy < y1 and grown[(sy - y0) * rw + (sx - x0)]:
            return False
        i = (sy * w + sx) * 3
        return is_bg(px[i], px[i + 1], px[i + 2])

    filled = []
    for y in range(rh):
        for x in range(rw):
            if not grown[y * rw + x]:
                continue
            radius, tries = 10.0, 0
            while True:
                sx = x0 + x + int(rng.uniform(-radius, radius))
                sy = y0 + y + int(rng.uniform(-radius, radius))
                if clean(sx, sy):
                    break
                tries += 1
                if tries % 10 == 0:
                    radius *= 1.4
            s, d = (sy * w + sx) * 3, ((y0 + y) * w + x0 + x) * 3
            px[d:d + 3] = px[s:s + 3]
            filled.append(d)

    # Soften the copied pixels slightly so the patch reads as print grain, not static.
    src = bytes(px)
    for d in filled:
        for c in range(3):
            i = d + c
            px[i] = (src[i] * 4 + src[i - 3] + src[i + 3] + src[i - w * 3] + src[i + w * 3]) // 8
    return len(filled)


def clean(poster, regions, seed=4):
    """Return a copy of `poster` with the baked-in readouts in `regions` painted out.
    regions: ((x0, y0, x1, y1), is_background(r, g, b)) in poster pixels."""
    w, h = poster.get_size()
    px = bytearray(pygame.image.tobytes(poster, "RGB"))
    rng = random.Random(seed)
    for rect, is_bg in regions:
        print(f"painted out {paint_out(px, w, h, rect, is_bg, rng)} px in {rect}")
    return pygame.image.frombytes(bytes(px), (w, h), "RGB")


def letterbox(cleaned, out, matte, target=TARGET):
    """Scale the whole poster to fit `target` and save it."""
    w, h = cleaned.get_size()
    k = min(target[0] / w, target[1] / h)
    scaled = pygame.transform.smoothscale(cleaned, (round(w * k), round(h * k)))
    canvas = pygame.Surface(target)
    canvas.fill(matte)
    canvas.blit(scaled, scaled.get_rect(center=(target[0] // 2, target[1] // 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out} (scale {k:.4f})")


def compose(cleaned, out, pieces, matte, size=PORTRAIT):
    """Cut `pieces` out of the poster and place them: each is ((sx, sy, sw, sh), (dx, dy, dw, dh))."""
    canvas = pygame.Surface(size)
    canvas.fill(matte)
    for src, dst in pieces:
        piece = cleaned.subsurface(pygame.Rect(src))
        canvas.blit(pygame.transform.smoothscale(piece, (dst[2], dst[3])), (dst[0], dst[1]))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out}")


def prepare(src, out, regions, matte):
    """Landscape background: paint out `regions`, letterbox to the screen. Returns the cleaned poster."""
    pygame.init()
    cleaned = clean(pygame.image.load(str(src)), regions)
    letterbox(cleaned, out, matte)
    return cleaned
