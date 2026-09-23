r"""Turn retface2.png into the orbit face's background.

Paints out the baked-in coordinates, date, weather, readings and the orbiting
satellite (the clock draws live ones), then scales the poster to fit 1600x720.
The flip-clock digits are left alone: the face covers those panels completely.

    .venv\Scripts\python.exe tools\prep_orbit.py
"""
from pathlib import Path

from poster import prepare

ROOT = Path(__file__).resolve().parent.parent


def is_dark(r, g, b):
    return r < 70 and g < 85


if __name__ == "__main__":
    prepare(
        ROOT / "retface2.png",
        ROOT / "assets" / "faces" / "orbit" / "background.png",
        regions=(
            ((545, 70, 1145, 122), is_dark),     # LAT / LON
            ((90, 565, 470, 730), is_dark),      # day and date
            ((560, 560, 945, 730), is_dark),     # weather icon, temperature, summary
            ((1255, 560, 1468, 604), is_dark),   # wind value
            ((1255, 620, 1468, 666), is_dark),   # humidity value
            ((1255, 683, 1468, 728), is_dark),   # pressure value
            ((1798, 335, 1844, 380), is_dark),   # satellite
        ),
        matte=(1, 12, 16),  # the poster's own outer colour
    )
