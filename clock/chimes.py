"""Hourly (and optionally half-hourly) chimes, with quiet hours."""
from pathlib import Path

import pygame

from .schedule import in_window

SOUNDS = Path(__file__).resolve().parent.parent / "assets" / "sounds"
EXTS = (".wav", ".ogg", ".oga", ".mp3")


def available():
    """Chime names, from the files in assets/sounds."""
    return sorted(p.stem for p in SOUNDS.iterdir() if p.suffix.lower() in EXTS)


class Chimes:
    def __init__(self, config):
        self.config = config
        self.sound = None
        self.last_slot = None
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as exc:      # no audio device (e.g. screenshot mode)
                print(f"chimes: no audio: {exc}")
                return
        self.apply()

    @property
    def cfg(self):
        return self.config["chime"]

    def apply(self):
        """Pick up the current config: sound and volume."""
        self.select(self.cfg["sound"])

    def select(self, name):
        if not pygame.mixer.get_init():
            return
        for ext in EXTS:
            path = SOUNDS / f"{name}{ext}"
            if path.exists():
                self.sound = pygame.mixer.Sound(str(path))
                self.sound.set_volume(float(self.cfg.get("volume", 0.8)))
                return
        print(f"chimes: no sound called {name!r}; have {available()}")

    def preview(self, name):
        """Play `name` once at the current volume without changing the selection."""
        if pygame.mixer.get_init():
            for ext in EXTS:
                path = SOUNDS / f"{name}{ext}"
                if path.exists():
                    s = pygame.mixer.Sound(str(path))
                    s.set_volume(float(self.cfg.get("volume", 0.8)))
                    s.play()
                    return

    def is_quiet(self, now):
        return in_window(now.time(), self.cfg.get("quiet_from", "00:00"), self.cfg.get("quiet_to", "00:00"))

    def play(self):
        if self.sound:
            self.sound.play()

    def tick(self, now):
        """Call every frame. Chimes once when the hour (or half hour) turns over."""
        slot = (now.hour, now.minute >= 30 if self.cfg.get("half_hour") else 0)
        if self.last_slot is None:
            self.last_slot = slot         # starting up: don't chime for the slot we're already in
            return
        if slot != self.last_slot:
            self.last_slot = slot
            if self.cfg.get("enabled", True) and not self.is_quiet(now):
                self.play()
