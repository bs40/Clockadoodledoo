r"""Turn the control-room mockup into the control face's backgrounds (landscape and portrait).

Paints out the baked-in date, time, the weather table's values and the values of the right-hand
column (crew, altitude, velocity, next orbit: the face draws all of them live; the labels stay),
letterboxes to 1600x720, and composes a 720x1600 portrait version: the window onto the Earth with
the crew on top, the cleared date-and-time corner below it, then the weather table beside the
right-hand column and, under the table, the radar console.

    .venv\Scripts\python.exe tools\prep_control.py
"""
from pathlib import Path

from poster import compose, prepare

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "retro_space_clock_03_control_room.png"
FACE = ROOT / "assets" / "faces" / "control"
MATTE = (7, 11, 15)


def is_panel(r, g, b):
    """The dark teal panels and their pale teal streaks and rules, but not the cream lettering
    or the near-black halo printed round it."""
    return g >= 7 and r < 50


if __name__ == "__main__":
    cleaned = prepare(
        SRC, FACE / "background.png", width=2000, matte=MATTE,
        regions=(
            ((92, 52, 580, 108), is_panel),            # date
            ((92, 118, 630, 292), is_panel),           # time
            ((280, 340, 474, 392), is_panel),          # weather values: temperature,
            ((280, 410, 474, 460), is_panel),          # humidity,
            ((280, 478, 474, 528), is_panel),          # pressure,
            ((280, 546, 474, 599), is_panel),          # wind
            ((1766, 124, 1830, 172), is_panel),        # crew,
            ((1766, 262, 1950, 310), is_panel),        # altitude,
            ((1766, 400, 1950, 448), is_panel),        # velocity,
            ((1766, 543, 1950, 590), is_panel),        # next orbit
        ),
    )
    compose(cleaned, FACE / "portrait.png", matte=MATTE, pieces=(
        ((596, 28, 800, 792), (0, 0, 720, 713)),            # the window, the Earth and the crew
        ((50, 40, 600, 240), (0, 713, 720, 288)),           # the date-and-time corner
        ((55, 316, 432, 294), (14, 1020, 432, 294)),        # the weather table
        ((1746, 56, 232, 558), (474, 1020, 232, 558)),      # crew, altitude, velocity, next orbit
        ((296, 649, 290, 166), (14, 1330, 432, 248)),       # the radar console
    ))
