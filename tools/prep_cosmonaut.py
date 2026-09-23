r"""Turn retface4.png into the cosmonaut face's background.

Paints out the baked-in date, time and weather readouts (the clock draws live
ones in their place), then scales the poster to fit 1600x720.

    .venv\Scripts\python.exe tools\prep_cosmonaut.py
"""
from pathlib import Path

from poster import prepare

ROOT = Path(__file__).resolve().parent.parent


def is_red(r, g, b):
    return r > 150 and g < 80


def is_navy(r, g, b):
    return r < 60 and g < 90


if __name__ == "__main__":
    prepare(
        ROOT / "retface4.png",
        ROOT / "assets" / "faces" / "cosmonaut" / "background.png",
        regions=(
            ((900, 118, 1400, 205), is_red),    # date
            ((815, 205, 1395, 475), is_red),    # time
            ((1624, 50, 1918, 520), is_navy),   # weather column, right of the divider rule
        ),
        matte=(14, 21, 26),  # the poster's own outer colour
    )
