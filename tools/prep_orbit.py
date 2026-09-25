r"""Turn retface2.png into the orbit face's backgrounds (landscape and portrait).

Paints out the baked-in coordinates, date, weather, readings and the orbiting satellite
(the clock draws live ones), letterboxes to 1600x720, and composes a 720x1600 portrait
version from the globe, the title bar and the three flip-clock panels; the face draws the
lower panels itself.

    .venv\Scripts\python.exe tools\prep_orbit.py
"""
from pathlib import Path

from poster import compose, prepare

ROOT = Path(__file__).resolve().parent.parent
FACE = ROOT / "assets" / "faces" / "orbit"
MATTE = (1, 12, 16)  # the poster's own outer colour


def is_dark(r, g, b):
    return r < 70 and g < 85


if __name__ == "__main__":
    cleaned = prepare(
        ROOT / "retface2.png", FACE / "background.png",
        regions=(
            ((545, 70, 1145, 122), is_dark),     # LAT / LON
            ((90, 565, 470, 730), is_dark),      # day and date
            ((560, 560, 945, 730), is_dark),     # weather icon, temperature, summary
            ((1255, 560, 1468, 604), is_dark),   # wind value
            ((1255, 620, 1468, 666), is_dark),   # humidity value
            ((1255, 683, 1468, 728), is_dark),   # pressure value
            ((1798, 335, 1844, 380), is_dark),   # satellite
            ((1622, 538, 1662, 578), is_dark),   # first letter of the slogan, under the globe
        ),
        matte=MATTE,
    )
    compose(cleaned, FACE / "portrait.png", matte=(2, 18, 24), pieces=(
        ((1215, 30, 727, 500), (0, 0, 720, 495)),        # globe, moon, orbit
        ((40, 50, 1160, 90), (0, 500, 720, 56)),         # EARTH ORBIT / LAT / LON bar
        ((40, 150, 1160, 350), (0, 560, 720, 217)),      # hours, minutes, seconds panels
    ))
