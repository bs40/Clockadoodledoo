r"""Turn the rainbow-valley mockup into the rainbow face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all of
them live) and letterboxes to 1600x720. Behind the readouts lies an out-of-focus night sky and
big blurred flowers (bokeh), with no fine texture to copy, so the lettering and its dark outline
are inpainted (prep_colony.inpaint()): a smooth surface joining the hole's edges, with the faint
grain of the picture nearby laid over it.

The 720x1600 portrait version puts the sun, the rainbow and the winding road on top. Below it the
cleared column (upside down, so the blurred flowers meet the flowers at the foot of the art) and
its mirror image make a dark bokeh card for the readouts; the foot of the art goes out of focus
and fades into it, like a shallow depth of field.

It also writes two grey masks, poster-sized (2000 px wide), for the face's lighting effects:
arcs.png, the rainbow's bands above the mountains (a light passes outward across them), and
sunlit.png, the sky and bands around the sun above the mountains (the sun's glow breathes).

    .venv\Scripts\python.exe tools\prep_rainbow.py
"""
from pathlib import Path

import pygame

from poster import letterbox
from prep_colony import inpaint

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "psychedelic_clock_01_rainbow_valley.png"
FACE = ROOT / "assets" / "faces" / "rainbow"
MATTE = (8, 7, 7)
WIDTH = 2000

ART = (870, 14, 840, 832)             # portrait: the sun, rainbow and road (poster x, y, w, h)
ART_H = 713                           # ... placed 720 x ART_H at the top
COLUMN = (44, 18, 400, 806)           # portrait: the cleared column inside the frame, for the card
FADE = 230                            # rows over which the art goes soft and fades into the card

ARCS = (1285, 380, 372)               # the rainbow's bands: centre and outer radius
SUN = (1285, 500, 300)                # the sun's disc and how far its glow reaches


def is_ink(r, g, b):
    """The peach time and date and the amber icons and values, not the dark bokeh behind them
    (the blurred clouds and flowers there are much darker, the orange flower redder)."""
    return r > 170 and g > 120 and g > r * 0.6


def blurred(surf, k):
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(w // k, 1), max(h // k, 1)))
    return pygame.transform.smoothscale(small, (w, h))


def is_mountain(r, g, b):
    """The blue mountains (and their pale snowy peaks), not the bands, clouds or flowers."""
    return b > r + 8


def is_band(r, g, b):
    """Rainbow bands, the sun and the clouds by them, not the dark blue sky between arcs."""
    return r > b + 12 or r > 170


def masks(cleaned):
    """arcs.png and sunlit.png (see above): white where the light may fall, soft-edged."""
    w, h = cleaned.get_size()
    px = pygame.image.tobytes(cleaned, "RGB")

    def at(x, y):
        i = (y * w + x) * 3
        return px[i], px[i + 1], px[i + 2]

    x0, x1 = ARCS[0] - ARCS[2] - 4, ARCS[0] + ARCS[2] + 4
    horizon = {}                                       # first mountain pixel down each column
    for x in range(x0, x1):
        horizon[x] = next((y for y in range(400, 640) if all(is_mountain(*at(x, y + k)) for k in range(3))), 560)
    smooth = {x: sorted(horizon[min(max(xx, x0), x1 - 1)] for xx in range(x - 6, x + 7))[6] for x in horizon}
    for name, (cx, cy, radius), wanted in (("arcs", ARCS, is_band), ("sunlit", SUN, lambda r, g, b: r > b)):
        mask = pygame.Surface((w, h))
        for x in range(max(cx - radius, x0), min(cx + radius, x1)):
            for y in range(max(cy - radius, 0), smooth[x] - 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius and wanted(*at(x, y)):
                    mask.set_at((x, y), (255, 255, 255))
        pygame.image.save(blurred(mask, 3), str(FACE / f"{name}.png"))
        print(f"wrote {name}.png")


def portrait(cleaned, out):
    canvas = pygame.Surface((720, 1600))
    canvas.fill(MATTE)
    card_h = 1600 - ART_H + FADE
    half = pygame.transform.smoothscale(cleaned.subsurface(COLUMN), (360, card_h))
    half = pygame.transform.flip(half, False, True)            # blurred flowers at the top
    card = pygame.Surface((720, card_h))                         # the dark side of the column
    card.blit(pygame.transform.flip(half, True, False), (0, 0))  # in the middle, under the text
    card.blit(half, (360, 0))
    card = blurred(card, 6)                                      # soften the mirror's join
    shade = pygame.Surface(card.get_size())                      # darker towards the bottom
    for y in range(card_h):
        v = int(255 * (0.78 - 0.18 * y / card_h))
        shade.fill((v, v, v), (0, y, 720, 1))
    card.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    canvas.blit(card, (0, ART_H - FADE))

    art = pygame.transform.smoothscale(cleaned.subsurface(ART), (720, ART_H))
    soft = blurred(art, 10)
    for y in range(ART_H):                                       # the foot goes out of focus ...
        k = min(max((y - (ART_H - FADE * 1.25)) / FADE, 0.0), 1.0)
        row = art.subsurface((0, y, 720, 1)).copy()
        if k > 0:
            blur_row = soft.subsurface((0, y, 720, 1)).copy()
            blur_row.set_alpha(int(255 * k))
            row.blit(blur_row, (0, 0))
        fade = min(max((ART_H - y) / FADE, 0.0), 1.0)            # ... and then into the card
        row.set_alpha(int(255 * fade * fade * (3 - 2 * fade)))
        canvas.blit(row, (0, y))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    cleaned = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    inpaint(cleaned, (56, 36, 764, 270), is_ink, grow=8)        # the time
    inpaint(cleaned, (84, 278, 614, 346), is_ink, grow=7)       # the date
    inpaint(cleaned, (52, 356, 378, 806), is_ink, grow=7)       # icons and values
    letterbox(cleaned, FACE / "background.png", MATTE)
    portrait(cleaned, FACE / "portrait.png")
    masks(cleaned)
