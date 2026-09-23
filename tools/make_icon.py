r"""Draw assets/icon.png, the launcher icon: a dark tile with the clock's cream digits and amber sun.

    .venv\Scripts\python.exe tools\make_icon.py
"""
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pygame

from clock import ui

SIZE, K = 256, 4
OUT = Path(__file__).resolve().parent.parent / "assets" / "icon.png"

pygame.init()
s = SIZE * K
big = pygame.Surface((s, s), pygame.SRCALPHA)
pygame.draw.rect(big, ui.INK, (0, 0, s, s), border_radius=s // 5)
pygame.draw.rect(big, (190, 186, 170), (6 * K, 6 * K, s - 12 * K, s - 12 * K), 3 * K, border_radius=s // 6)
glow = pygame.Surface((s, s), pygame.SRCALPHA)
for r in range(88 * K, 30 * K, -K):
    t = 1 - (r - 30 * K) / (58 * K)
    pygame.draw.circle(glow, (*ui.AMBER, int(60 * t * t)), (s // 2, 96 * K), r)
big.blit(glow, (0, 0))
pygame.draw.circle(big, (250, 214, 140), (s // 2, 96 * K), 30 * K)
pygame.draw.circle(big, (255, 236, 186), (s // 2, 96 * K), 20 * K)
for a in (0, 60, 120, 180, 240, 300):
    import math
    dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
    pygame.draw.line(big, ui.AMBER, (s // 2 + 40 * K * dx, 96 * K + 40 * K * dy),
                     (s // 2 + 52 * K * dx, 96 * K + 52 * K * dy), 3 * K)
digits = ui.fixed_digits("19:42", ui.WIDE, 46 * K, ui.CREAM)[0]
big.blit(digits, digits.get_rect(center=(s // 2, 186 * K)))
pygame.image.save(pygame.transform.smoothscale(big, (SIZE, SIZE)), str(OUT))
print("wrote", OUT)
