r"""Turn the ringed-planet mockup into the rings face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all
of them live) and letterboxes to 1600x720. Behind the readouts lies a dark maroon sky that
shades to black lower down, the rim of a pink planet and the edge of orange clouds, so the
lettering and its soft dark halo are inpainted (prep_colony.inpaint(): a smooth surface that
joins the hole's edges, with the grain of clean stretches nearby laid over it) rather than
covered with copied blocks, which would show seams on the gradient.

The 720x1600 portrait version puts the ringed planet, its rings and the lake on top and, below
them, the cleared column and its mirror image as a card for the readouts; the picture's lower
edge fades into the card.

    .venv\Scripts\python.exe tools\prep_rings.py
"""
from pathlib import Path

import pygame

from poster import PORTRAIT, letterbox
from prep_colony import inpaint

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "psychedelic_clock_04_ringed_planet.png"
FACE = ROOT / "assets" / "faces" / "rings"
MATTE = (8, 7, 8)
WIDTH = 2000

PLANET = (1010, 12, 880, 806)            # portrait: the planet, its rings and the lake ...
PLANET_TO = (0, 0, 720, 659)
FADE = 90                                # rows over which the picture's foot fades out ...
COLUMN = (26, 50, 268, 760)              # ... into the cleared column, with its mirror image,
COLUMN_TO = (0, 659 - FADE, 360, 1600 - 659 + FADE)       # stretched a touch to the bottom


def is_pink(r, g, b):
    """The pink time and date (the planet's rim behind the date is redder and darker)."""
    return r > 170 and g > 100 and b > 95


def is_coral(r, g, b):
    """The coral icons and values, not the orange clouds beside them (less blue in those)."""
    return r > 160 and g > 85 and b > 60 and g - b < 55


def portrait(cleaned, out):
    canvas = pygame.Surface(PORTRAIT)
    canvas.fill(MATTE)
    column = pygame.transform.smoothscale(cleaned.subsurface(COLUMN), COLUMN_TO[2:])
    canvas.blit(column, COLUMN_TO[:2])
    canvas.blit(pygame.transform.flip(column, True, False), (360, COLUMN_TO[1]))
    art = pygame.transform.smoothscale(cleaned.subsurface(PLANET), PLANET_TO[2:]).convert_alpha()
    ah = art.get_height()
    for row in range(ah - FADE, ah):                     # fade the lake's foot into the column
        a = (ah - row) / FADE
        art.fill((255, 255, 255, round(255 * a * a * (3 - 2 * a))), (0, row, art.get_width(), 1),
                 special_flags=pygame.BLEND_RGBA_MULT)
    canvas.blit(art, PLANET_TO[:2])
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    cleaned = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    inpaint(cleaned, (66, 36, 730, 262), is_pink, grow=11)       # the time
    inpaint(cleaned, (84, 262, 612, 344), is_pink, grow=8)       # the date
    inpaint(cleaned, (66, 356, 380, 800), is_coral, grow=6)      # icons and values
    letterbox(cleaned, FACE / "background.png", MATTE)
    portrait(cleaned, FACE / "portrait.png")
