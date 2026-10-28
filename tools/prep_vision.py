r"""Turn the cosmic-vision mockup into the vision face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all
of them live) and letterboxes to 1600x720. The readouts sit on a dark brown, softly mottled
backdrop that the art's swirls fade into, and the right of the time reaches the hair and the
starburst's rays, so the lettering (and its soft dark halo) is inpainted with prep_colony.py's
inpaint(): a smooth estimate of the surrounding picture with the fine grain of clean stretches
nearby laid over it.

The 720x1600 portrait version puts the woman's face, the third-eye starburst and the start of
the tunnel of faces on top and, below them, the cleared column and its mirror image as a card
for the readouts.

    .venv\Scripts\python.exe tools\prep_vision.py
"""
from pathlib import Path

import pygame

from poster import compose, letterbox
from prep_colony import inpaint

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "psychedelic_clock_02_cosmic_vision.png"
FACE = ROOT / "assets" / "faces" / "vision"
MATTE = (10, 8, 8)
WIDTH = 2000

ART = (740, 16, 760, 840)            # portrait: the face, the starburst and the first of the tunnel
ART_H = 796                          # its height on the portrait canvas (720 wide)
COLUMN = (0, 0, 290, 878)            # the cleared column and frame, mirrored for the portrait card


def is_ink(r, g, b):
    """The peach lettering and icons, not the orange rays or the green and pink swirls."""
    return r > 150 and g > 105 and r - g < 95 and g - b > 20 and b < 200


def build():
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    inpaint(poster, (60, 36, 716, 352), is_ink, grow=9)          # time and date
    inpaint(poster, (60, 352, 374, 806), is_ink, grow=8)         # the weather column
    letterbox(poster, FACE / "background.png", MATTE)
    return poster


if __name__ == "__main__":
    cleaned = build()
    x, y, cw, ch = COLUMN
    card_h = 1600 - ART_H
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        (ART, (0, 0, 720, ART_H)),
        (COLUMN, (0, ART_H, 360, card_h)),
        (COLUMN, (360, ART_H, 360, card_h), "mirror"),
    ))
