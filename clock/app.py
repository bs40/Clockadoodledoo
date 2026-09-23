"""Main loop: opens the display, runs the active face, chimes, brightness and settings."""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
DEFAULTS = ROOT / "config.default.json"
HOLD_MS = 700          # press-and-hold this long to open settings
UPDATE_FLAG = ROOT / ".update-pending"   # written by pi/update.sh when new code has been installed
UPDATE_MAX_WAIT_H = 30                   # restart for an update anyway after this long


def load_config():
    """config.json holds this clock's settings; anything it lacks comes from config.default.json."""
    with open(DEFAULTS, encoding="utf-8") as fh:
        config = json.load(fh)
    if CONFIG.exists():
        with open(CONFIG, encoding="utf-8") as fh:
            saved = json.load(fh)
        for key, value in saved.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    return config


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Clockadoodledoo")
    p.add_argument("--face", help="face to show (default: from config.json)")
    p.add_argument("--fullscreen", action="store_true", help="fill the screen (use this on the Pi)")
    p.add_argument("--scale", type=float, default=1.0, help="window scale when not fullscreen, e.g. 0.75")
    p.add_argument("--demo", action="store_true", help="use the mockup's weather values, no network")
    p.add_argument("--time", help="pretend it is this time, e.g. 2026-09-23T19:42:17")
    p.add_argument("--screenshot", metavar="PNG", help="render one frame to a file and exit")
    p.add_argument("--settings", action="store_true", help="start with the settings panel open")
    p.add_argument("--chime", nargs="?", const="", metavar="NAME",
                   help="play the configured chime (or NAME) and exit; --chime list shows the names")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.screenshot:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    import pygame
    from .chimes import Chimes, available
    from .display import Backlight
    from .schedule import in_window
    from .faces import FACES
    from .settings import Settings
    from .weather import Weather

    config = load_config()
    if args.chime is not None:
        if args.chime == "list":
            print("\n".join(available()))
            return
        pygame.init()
        chimes = Chimes(config)
        if args.chime:
            chimes.select(args.chime)
        chimes.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
        return
    pygame.init()
    pygame.display.set_caption("Clockadoodledoo")

    names = list(FACES)
    current = names.index(args.face or config["face"])
    fw, fh = FACES[names[current]].size
    if args.fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode((round(fw * args.scale), round(fh * args.scale)))

    weather = Weather(config, demo=args.demo)
    if args.screenshot:
        weather.fetch_once()
    else:
        weather.start()
    ctx = SimpleNamespace(config=config, config_path=CONFIG, weather=weather)
    chimes = ctx.chimes = Chimes(config)
    backlight = Backlight(config)
    loaded = {}

    def face_at(index):
        if index not in loaded:
            loaded[index] = FACES[names[index]](ctx)
        return loaded[index]

    def show_face(name):
        nonlocal current
        current = names.index(name)

    def settings_saved():
        chimes.apply()
        backlight.reapply()
        show_face(config["face"])

    def quit_app():
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    settings = Settings(ctx, names, on_save=settings_saved, on_face=show_face, on_exit=quit_app)
    if args.settings:
        settings.open()

    offset = datetime.fromisoformat(args.time) - datetime.now() if args.time else None
    canvas = screen if screen.get_size() == (fw, fh) else pygame.Surface((fw, fh))
    ticker = pygame.time.Clock()
    press = None               # (ticks, canvas position) while a finger or button is down
    scale, origin = 1.0, (0, 0)

    def to_canvas(pos):
        return ((pos[0] - origin[0]) / scale, (pos[1] - origin[1]) / scale)

    def update_due(now):
        """New code is installed: restart during the dim hours, when nobody is looking."""
        if not UPDATE_FLAG.exists() or settings.visible:
            return False
        waited_h = (now.timestamp() - UPDATE_FLAG.stat().st_mtime) / 3600
        return in_window(now.time(), config["display"]["dim_from"], config["display"]["dim_to"])             or waited_h > UPDATE_MAX_WAIT_H

    last_update_check = -60_000       # check straight away, then every 30 s
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and settings.visible:
                    settings.cancel()
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_s:
                    settings.open()
                elif event.key == pygame.K_SPACE and not settings.visible:
                    current = (current + 1) % len(names)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                press = (pygame.time.get_ticks(), to_canvas(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and press is not None:
                press = None
                pos = to_canvas(event.pos)
                if settings.visible:
                    settings.tap(pos)
                else:
                    current = (current + 1) % len(names)      # a short tap: next face
        if press is not None and not settings.visible and pygame.time.get_ticks() - press[0] >= HOLD_MS:
            press = None
            settings.open()

        now = datetime.now().astimezone()
        if offset is not None:
            now += offset
        if pygame.time.get_ticks() - last_update_check > 30_000:
            last_update_check = pygame.time.get_ticks()
            if update_due(now):
                print("restarting for update:", UPDATE_FLAG.read_text().strip())
                UPDATE_FLAG.unlink()
                pygame.quit()
                os.execv(sys.executable, [sys.executable] + sys.argv)
        chimes.tick(now)
        backlight.tick(now)
        face_at(current).draw(canvas, now)
        settings.draw(canvas)
        backlight.draw(canvas)

        if canvas is not screen:
            sw, sh = screen.get_size()
            scale = min(sw / fw, sh / fh)
            scaled = pygame.transform.smoothscale(canvas, (round(fw * scale), round(fh * scale)))
            rect = scaled.get_rect(center=(sw // 2, sh // 2))
            origin = rect.topleft
            screen.fill((0, 0, 0))
            screen.blit(scaled, rect)

        if args.screenshot:
            pygame.image.save(canvas, args.screenshot)
            break
        pygame.display.flip()
        ticker.tick(config["fps"])

    pygame.quit()
