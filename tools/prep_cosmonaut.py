r"""Turn retface4.png into the cosmonaut face's backgrounds (landscape and portrait).

Paints out the baked-in date, time and weather readouts (the clock draws live ones in their
place), letterboxes the poster to 1600x720, and composes a 720x1600 portrait version from
three bands: the cosmonaut, the red sun, and the skyline with the slogan.

    .venv\Scripts\python.exe tools\prep_cosmonaut.py
"""
from pathlib import Path

from poster import compose, prepare

ROOT = Path(__file__).resolve().parent.parent
FACE = ROOT / "assets" / "faces" / "cosmonaut"
MATTE = (14, 21, 26)  # the poster's own outer colour


def is_red(r, g, b):
    return r > 150 and g < 80


def is_navy(r, g, b):
    return r < 60 and g < 90


if __name__ == "__main__":
    cleaned = prepare(
        ROOT / "retface4.png", FACE / "background.png",
        regions=(
            ((900, 118, 1400, 205), is_red),    # date
            ((815, 205, 1395, 475), is_red),    # time
            ((1624, 50, 1918, 520), is_navy),   # weather column, right of the divider rule
        ),
        matte=MATTE,
    )
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        ((0, 100, 780, 650), (0, 0, 720, 600)),          # the cosmonaut
        ((790, 100, 660, 642), (0, 600, 720, 700)),      # the red sun (time goes here)
        ((1180, 500, 762, 309), (0, 1300, 720, 300)),    # skyline, rocket base, slogan
    ))
