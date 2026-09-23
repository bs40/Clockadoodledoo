r"""Turn pixface1.png into the pixel-city face's background.

Paints out the baked-in date, time, weather icon, temperature, summary and the three values
(the cyan labels and the divider are kept), then scales the poster to fit 1600x720.

    .venv\Scripts\python.exe tools\prep_pixel.py
"""
from pathlib import Path

from poster import prepare

ROOT = Path(__file__).resolve().parent.parent


def is_panel(r, g, b):
    return r < 42 and g < 42 and b < 48


if __name__ == "__main__":
    prepare(
        ROOT / "pixface1.png",
        ROOT / "assets" / "faces" / "pixel" / "background.png",
        regions=(
            ((1395, 55, 1870, 125), is_panel),     # date
            ((1395, 128, 1870, 305), is_panel),    # time
            ((1395, 318, 1880, 475), is_panel),    # weather icon, temperature, summary
            ((1640, 540, 1880, 725), is_panel),    # humidity, wind, pressure values
        ),
        matte=(4, 4, 6),
    )
