r"""Turn the rocket-launch mockup into the launch face's backgrounds (landscape and portrait).

Covers the baked-in date, time and the weather column (icons, values and labels: the face
draws all of them live) with starry sky copied from beside the rocket's nose, letterboxes to
1600x720, and composes a 720x1600 portrait version: the rocket on top and, below it, the
cleared column and its mirror image as a card for the readouts.

    .venv\Scripts\python.exe tools\prep_launch.py
"""
from pathlib import Path

from poster import compose, prepare, resurface

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_01_rocket_launch.png"
FACE = ROOT / "assets" / "faces" / "launch"
MATTE = (8, 9, 10)
SKY = ((645, 30, 790, 185), (645, 185, 735, 280))     # clean stars beside the rocket's nose


def is_exhaust(r, g, b):
    """The glow and its dim red fringe: anything brighter than the night sky and its halos."""
    return r > 45


def not_lettering(r, g, b):
    """Everything but the cream lettering, which lies partly over the exhaust's glow."""
    return not (r > 150 and g > 140 and b > 110 and r - b < 50)


if __name__ == "__main__":
    cleaned = prepare(
        SRC, FACE / "background.png", width=2000, matte=MATTE,
        regions=(
            ((80, 600, 530, 845), not_lettering),     # pressure and wind over the glow: first the
        ),                                            # letters go, then the sky around them below
        patches=(
            ((58, 55, 660, 340), SKY),                 # date and time
            ((58, 340, 420, 600), SKY),                # sun, temperature, CLEAR, drop, humidity
            ((58, 600, 455, 842), SKY, is_exhaust),    # pressure and wind, beside the exhaust
        ),
    )
    card = cleaned.copy()                              # portrait readout card: the cleared column
    resurface(card, (58, 600, 455, 842), SKY)          # with no exhaust, and its mirror image
    card.blit(cleaned, (390, 0), (390, 0, 1610, 872))
    compose(card, FACE / "portrait.png", matte=MATTE, pieces=(
        ((395, 22, 860, 830), (0, 0, 720, 695)),                       # the rocket and its exhaust
        ((14, 0, 376, 872), (0, 695, 360, 905)),
        ((14, 0, 376, 872), (360, 695, 360, 905), "mirror"),
    ))
