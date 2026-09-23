"""Screen brightness on a daily schedule.

Sets the panel's backlight over DDC/CI with ddcutil (the Waveshare screen supports it). Where
that isn't available, such as on the development PC, a translucent overlay dims the picture
instead so the schedule can still be seen working.
"""
import subprocess
import threading

import pygame

from .schedule import in_window


class Backlight:
    def __init__(self, config):
        self.cfg = config["display"]
        self.current = None       # brightness last applied, 0-100
        self.hardware = None      # True once ddcutil has worked, False once it has failed
        self.overlay = None

    def target(self, now):
        night = in_window(now.time(), self.cfg["dim_from"], self.cfg["dim_to"])
        return int(self.cfg["night"] if night else self.cfg["day"])

    def reapply(self):
        self.current = None       # settings changed: apply again on the next tick

    def tick(self, now):
        level = self.target(now)
        if level != self.current:
            self.current = level
            threading.Thread(target=self._set_hardware, args=(level,), daemon=True).start()

    def _set_hardware(self, level):
        try:
            done = subprocess.run(["ddcutil", "setvcp", "10", str(level)],
                                  capture_output=True, text=True, timeout=30)
            ok = done.returncode == 0
            if not ok:
                print(f"backlight: ddcutil failed: {done.stderr.strip()}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            ok = False
            if self.hardware is None:
                print(f"backlight: no ddcutil ({exc.__class__.__name__}); dimming in software")
        self.hardware = ok

    def draw(self, surf):
        """Software fallback: darken the frame to match the wanted level."""
        if self.hardware is not False or self.current is None or self.current >= 100:
            return
        if self.overlay is None or self.overlay.get_size() != surf.get_size():
            self.overlay = pygame.Surface(surf.get_size())
        self.overlay.set_alpha(int(235 * (100 - self.current) / 100))
        surf.blit(self.overlay, (0, 0))
