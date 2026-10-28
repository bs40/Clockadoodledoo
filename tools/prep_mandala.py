r"""Turn the mandala-meditation mockup into the mandala face's backgrounds (landscape and portrait).

Removes the baked-in date, time and the weather column (icons and values: the face draws all of
them live) and letterboxes to 1600x720. Behind the readouts lie a dark teal sky, dim clouds, the
far mountains and the lake, all under a dark gradient, so the lettering and its soft dark halo
are inpainted (prep_colony.inpaint(): a smooth surface that joins the hole's edges, with the
grain of clean stretches nearby laid over it) rather than covered with copied blocks.

The 720x1600 portrait version puts the meditating figure, his mandala halo and the lake on top,
fading into a card for the readouts (the cleared column and its mirror image, blurred to its
broad shading, with print grain), and floats the big lotus at the foot.

    .venv\Scripts\python.exe tools\prep_mandala.py
"""
import math
import random
from pathlib import Path

import pygame

from poster import letterbox
from prep_colony import inpaint
from prep_explorer import _grain

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "face designs" / "psychedelic_clock_05_mandala_meditation.png"
FACE = ROOT / "assets" / "faces" / "mandala"
MATTE = (6, 10, 12)
WIDTH = 2000
INK = (245, 186, 82)
GAUGE = (131, 627)                    # the pressure icon's centre
# portrait pieces, (poster rect) -> (canvas rect); clock/faces/mandala.py maps its effects the same way
ART = ((765, 14, 855, 826), (0, 0, 720, 696))          # the figure, the halo and the lake
LOTUS = ((452, 680, 290, 178), (193, 1395, 334, 205))  # the big lotus on the left, at the foot
CARD = (36, 30, 273, 770)                              # the cleared column, for the readout card
GRAIN = ((24, 40, 100, 330),)                          # clear sky beside the time
FADE = 140


def is_ink(r, g, b):
    """The cream lettering and the golden icons and values, not the teal sky or the dim clouds."""
    return r > 150 and g > 110 and r - b > 30


def build():
    pygame.init()
    poster = pygame.image.load(str(SRC))
    w, h = poster.get_size()
    poster = pygame.transform.smoothscale(poster.convert(24), (WIDTH, round(h * WIDTH / w)))
    inpaint(poster, (80, 30, 690, 222), is_ink, grow=9)          # the time
    inpaint(poster, (100, 236, 612, 312), is_ink, grow=8)        # the date
    pygame.draw.circle(poster, INK, GAUGE, 42)                   # the gauge's dial is a shade
    inpaint(poster, (66, 350, 372, 792), is_ink, grow=8)         # lighter than the sky: it goes
    letterbox(poster, FACE / "background.png", MATTE)
    return poster


def _faded(piece, size, alpha):
    """`piece` scaled to `size` on a transparent surface, its opacity alpha(x, y) per pixel (0..1)."""
    w, h = size
    out = pygame.Surface(size, pygame.SRCALPHA)
    out.blit(pygame.transform.smoothscale(piece, size), (0, 0))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            mask.set_at((x, y), (255, 255, 255, round(255 * min(max(alpha(x, y), 0.0), 1.0))))
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _ease(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def card(cleaned, size):
    """The portrait's readout card: the cleared column and its mirror image, blurred to its
    broad shading (dark teal sky, the clouds' dim glow, the darker lake) so the mirrored clouds
    don't make a pattern, with the print grain of the clear sky beside the time laid over it."""
    w, h = size
    half = pygame.transform.smoothscale(cleaned.subsurface(pygame.Rect(CARD)), (w // 2, h))
    both = pygame.Surface(size)
    both.blit(half, (0, 0))
    both.blit(pygame.transform.flip(half, True, False), (w // 2, 0))
    smooth = pygame.transform.smoothscale(pygame.transform.smoothscale(both, (w // 40, h // 40)), size)
    grain, _, _ = _grain(cleaned, size, GRAIN, random.Random(11))
    px = bytearray(pygame.image.tobytes(smooth, "RGB"))
    for i in range(len(px)):
        px[i] = max(min(px[i] + grain[i], 255), 0)
    return pygame.image.frombytes(bytes(px), size, "RGB")


def portrait(cleaned, out):
    """The figure, halo and lake (ART) on top, fading over its last FADE rows into the readout
    card, with a lotus (LOTUS) floating at the foot."""
    canvas = pygame.Surface((720, 1600))
    top = ART[1][3] - FADE
    canvas.blit(card(cleaned, (720, 1600 - top)), (0, top))
    w, h = ART[1][2:]
    canvas.blit(_faded(cleaned.subsurface(pygame.Rect(ART[0])), (w, h),
                       lambda x, y: 1 - _ease((y - (h - FADE)) / FADE)), ART[1][:2])
    (lx, ly, lw, lh) = LOTUS[1]
    lotus = pygame.transform.smoothscale(cleaned.subsurface(pygame.Rect(LOTUS[0])), (lw, lh))

    def oval(x, y):                         # the petals and their reflection, fading to the edges;
        d = math.hypot((x - lw / 2) / (lw / 2), (y - lh * 0.55) / (lh * 0.55))      # the bluer water
        r, g, b, _ = lotus.get_at((x, y))                                         # round them faintly
        return (1 - _ease((d - 0.45) / 0.5)) * (0.2 + 0.8 * _ease((r - b - 10) / 70))

    canvas.blit(_faded(lotus, (lw, lh), oval), (lx, ly))
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    portrait(build(), FACE / "portrait.png")
