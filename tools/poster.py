"""Shared steps for turning a poster mockup into a face background.

A mockup has example readouts baked into it. paint_out() removes them by copying
nearby clean background over them; prepare() does that for a list of regions and
then letterboxes the poster to the screen size.
"""
import random

import pygame

TARGET = (1600, 720)
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


def prepare(src, out, regions, matte):
    """regions: ((x0, y0, x1, y1), is_background(r, g, b)) in source pixels.
    matte: colour for the letterbox bars, normally the poster's own outer colour."""
    pygame.init()
    poster = pygame.image.load(str(src))
    w, h = poster.get_size()
    px = bytearray(pygame.image.tobytes(poster, "RGB"))
    rng = random.Random(4)
    for rect, is_bg in regions:
        print(f"painted out {paint_out(px, w, h, rect, is_bg, rng)} px in {rect}")
    cleaned = pygame.image.frombytes(bytes(px), (w, h), "RGB")

    k = min(TARGET[0] / w, TARGET[1] / h)
    scaled = pygame.transform.smoothscale(cleaned, (round(w * k), round(h * k)))
    canvas = pygame.Surface(TARGET)
    canvas.fill(matte)
    canvas.blit(scaled, scaled.get_rect(center=(TARGET[0] // 2, TARGET[1] // 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out} (scale {k:.4f})")
