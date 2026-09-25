r"""Turn pixface1.png into the pixel-city face's backgrounds (landscape and portrait).

Paints out the baked-in date, time, weather icon, temperature, summary and the three values
(the cyan labels and the divider are kept), letterboxes to 1600x720, and composes a 720x1600
portrait version from the middle of the street scene; the face draws its own panel below.

    .venv\Scripts\python.exe tools\prep_pixel.py
"""
from pathlib import Path

from poster import compose, prepare

ROOT = Path(__file__).resolve().parent.parent
FACE = ROOT / "assets" / "faces" / "pixel"
MATTE = (4, 4, 6)


def is_panel(r, g, b):
    return r < 42 and g < 42 and b < 48


if __name__ == "__main__":
    cleaned = prepare(
        ROOT / "pixface1.png", FACE / "background.png",
        regions=(
            ((1395, 55, 1870, 125), is_panel),     # date
            ((1395, 128, 1870, 305), is_panel),    # time
            ((1395, 318, 1880, 475), is_panel),    # weather icon, temperature, summary
            ((1640, 540, 1880, 725), is_panel),    # humidity, wind, pressure values
        ),
        matte=MATTE,
    )
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        ((330, 0, 720, 809), (0, 0, 720, 809)),          # the street, lantern and walkers
    ))
