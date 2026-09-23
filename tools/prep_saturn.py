r"""Turn retface3.png into the saturn face's background.

Paints out the baked-in day, date, time and weather values (the labels, the amber rule and the
slogan are kept), then scales the poster to fit 1600x720.

    .venv\Scripts\python.exe tools\prep_saturn.py
"""
from pathlib import Path

from poster import prepare

ROOT = Path(__file__).resolve().parent.parent


def is_sky(r, g, b):
    return r < 110 and g < 120 and b < 130


if __name__ == "__main__":
    prepare(
        ROOT / "retface3.png",
        ROOT / "assets" / "faces" / "saturn" / "background.png",
        regions=(
            ((1340, 50, 1905, 190), is_sky),     # day and date
            ((1385, 195, 1905, 385), is_sky),    # time
            ((1620, 395, 1905, 640), is_sky),    # the four weather values
        ),
        matte=(6, 12, 16),
    )
