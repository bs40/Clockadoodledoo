r"""Turn retface3.png into the saturn face's backgrounds (landscape and portrait).

Paints out the baked-in day, date, time and weather values (the labels, the amber rule and
the slogan are kept), letterboxes to 1600x720, and composes a 720x1600 portrait version:
the scenery on top and, below it, the starry text column with everything painted out.

    .venv\Scripts\python.exe tools\prep_saturn.py
"""
from pathlib import Path

from poster import clean, compose, prepare

ROOT = Path(__file__).resolve().parent.parent
FACE = ROOT / "assets" / "faces" / "saturn"
MATTE = (6, 12, 16)


def is_sky(r, g, b):
    return r < 110 and g < 120 and b < 130


if __name__ == "__main__":
    cleaned = prepare(
        ROOT / "retface3.png", FACE / "background.png",
        regions=(
            ((1340, 50, 1905, 190), is_sky),     # day and date
            ((1385, 195, 1905, 385), is_sky),    # time
            ((1620, 395, 1905, 640), is_sky),    # the four weather values
        ),
        matte=MATTE,
    )
    bare = clean(cleaned, (                      # portrait: the labels, rule and slogan go too
        ((1340, 190, 1385, 650), is_sky),        # amber rule
        ((1390, 395, 1625, 645), is_sky),        # TEMP / HUMIDITY / PRESSURE / WIND
        ((1380, 655, 1910, 790), is_sky),        # divider and SOMEWHERE OUT THERE
        ((1340, 590, 1942, 670), is_sky),        # mountain tops at the bottom of the column
    ), seed=7)
    compose(bare, FACE / "portrait.png", matte=MATTE, pieces=(
        ((240, 0, 720, 809), (0, 0, 720, 809)),          # Saturn, the peak and the moons
        ((1340, 0, 602, 660), (0, 809, 720, 791)),       # starry sky for the readouts
    ))
