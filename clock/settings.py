"""Touch settings panel, opened by press-and-hold.

Edits a draft copy of the config; Save writes config.json and applies the changes, Cancel
throws the draft away. The face carries on animating behind the panel.
"""
import copy
import json

import pygame

from . import ui
from .chimes import available
from .schedule import step_hhmm

PANEL = pygame.Rect(110, 50, 1380, 620)
COLS = (150, 830)              # left edge of each column
ROW0, ROW_H = 172, 66
BTN_W, BTN_H = 62, 54          # the < > buttons
CTRL_X = 290                   # controls start this far into a column
VALUE_W = 226
COL_TITLES = ("CHIME", "DISPLAY")

BG = (9, 19, 27)
BORDER = (122, 214, 228)
BUTTON = (24, 50, 62)
BUTTON_HI = (38, 84, 102)
TITLE = (250, 186, 92)
TEXT = ui.CREAM
DIM = ui.MUTED


def _pct(v):
    return f"{round(v * 100)}%"


class Settings:
    def __init__(self, ctx, faces, on_save, on_face, on_exit):
        self.ctx = ctx
        self.faces = list(faces)
        self.on_save = on_save
        self.on_face = on_face
        self.on_exit = on_exit
        self.visible = False
        self.draft = None
        self.buttons = []          # (rect, callback) rebuilt every draw
        self.flash = None          # (rect, until_ms) button feedback
        self.rows = self._rows()

    # ---- the rows, as (column, label, read, change) -----------------------------
    def _rows(self):
        d = lambda: self.draft

        def spin_time(section, key, minutes=30):
            return (lambda: d()[section][key],
                    lambda k: d()[section].__setitem__(key, step_hhmm(d()[section][key], k * minutes)))

        def spin_num(section, key, lo, hi, step, show):
            def change(k):
                d()[section][key] = round(min(max(d()[section][key] + k * step, lo), hi), 2)
            return (lambda: show(d()[section][key]), change)

        def spin_choice(section, key, options):
            def change(k):
                opts = options()
                d()[section][key] = opts[(opts.index(d()[section][key]) + k) % len(opts)]
            return (lambda: d()[section][key], change)

        def when():
            c = d()["chime"]
            return "OFF" if not c["enabled"] else ("EVERY HALF HOUR" if c["half_hour"] else "EVERY HOUR")

        def change_when(k):
            c = d()["chime"]
            modes = [(True, False), (True, True), (False, False)]
            i = modes.index((c["enabled"], c["half_hour"]))
            c["enabled"], c["half_hour"] = modes[(i + k) % 3]

        def face_change(k):
            f = self.faces
            d()["face"] = f[(f.index(d()["face"]) + k) % len(f)]
            self.on_face(d()["face"])

        def clock_change(k):
            d()["clock"]["24_hour"] = not d()["clock"]["24_hour"]

        return [
            (0, "SOUND", *spin_choice("chime", "sound", available)),
            (0, "CHIME", when, change_when),
            (0, "VOLUME", *spin_num("chime", "volume", 0.0, 1.0, 0.1, _pct)),
            (0, "QUIET FROM", *spin_time("chime", "quiet_from")),
            (0, "QUIET UNTIL", *spin_time("chime", "quiet_to")),
            (1, "FACE", lambda: d()["face"].upper(), face_change),
            (1, "DAY BRIGHTNESS", *spin_num("display", "day", 10, 100, 10, lambda v: f"{v}%")),
            (1, "NIGHT BRIGHTNESS", *spin_num("display", "night", 0, 100, 10, lambda v: f"{v}%")),
            (1, "DIM FROM", *spin_time("display", "dim_from")),
            (1, "DIM UNTIL", *spin_time("display", "dim_to")),
            (1, "CLOCK", lambda: "24 HOUR" if d()["clock"]["24_hour"] else "12 HOUR", clock_change),
        ]

    # ---- open / close ------------------------------------------------------------
    def open(self):
        self.draft = copy.deepcopy(self.ctx.config)
        self.draft["chime"]["volume"] = round(self.draft["chime"]["volume"], 1)
        self.visible = True

    def cancel(self):
        self.visible = False
        self.on_face(self.ctx.config["face"])

    def save(self):
        self.ctx.config.clear()
        self.ctx.config.update(self.draft)
        with open(self.ctx.config_path, "w", encoding="utf-8") as fh:
            json.dump(self.ctx.config, fh, indent=2)
        self.visible = False
        self.on_save()

    # ---- input -----------------------------------------------------------------------
    def tap(self, pos):
        for rect, action in self.buttons:
            if rect.collidepoint(pos):
                self.flash = (rect, pygame.time.get_ticks() + 120)
                action()
                return True
        return PANEL.collidepoint(pos)

    # ---- drawing ------------------------------------------------------------------------
    def _button(self, surf, rect, label, action, size=30, colour=TEXT):
        lit = self.flash and self.flash[0] == rect and pygame.time.get_ticks() < self.flash[1]
        pygame.draw.rect(surf, BUTTON_HI if lit else BUTTON, rect, border_radius=10)
        pygame.draw.rect(surf, BORDER, rect, 2, border_radius=10)
        t = ui.text(label, ui.LABEL_MED, size, colour, tracking=2)
        surf.blit(t, t.get_rect(center=rect.center))
        self.buttons.append((rect, action))

    def draw(self, surf):
        if not self.visible:
            return
        self.buttons = []
        panel = pygame.Surface(PANEL.size, pygame.SRCALPHA)
        panel.fill((*BG, 236))
        surf.blit(panel, PANEL.topleft)
        pygame.draw.rect(surf, BORDER, PANEL, 3, border_radius=18)
        ui.blit_text(surf, "SETTINGS", ui.LABEL_BOLD, 40, TITLE, (PANEL.centerx, PANEL.y + 42),
                     tracking=10, anchor="center")
        ui.blit_text(surf, "press and hold the clock to open this panel  -  tap a sound name to hear it",
                     ui.LABEL, 22, DIM, (PANEL.centerx, PANEL.y + 78), tracking=2, anchor="center")
        for i, title in enumerate(COL_TITLES):
            ui.blit_text(surf, title, ui.LABEL_MED, 24, BORDER, (COLS[i], ROW0 - 36), tracking=8)
            pygame.draw.line(surf, BORDER, (COLS[i], ROW0 - 8), (COLS[i] + 620, ROW0 - 8), 1)

        counts = [0, 0]
        for col, label, read, change in self.rows:
            x = COLS[col]
            y = ROW0 + counts[col] * ROW_H + ROW_H // 2
            counts[col] += 1
            ui.blit_text(surf, label, ui.LABEL_MED, 27, TEXT, (x, y), tracking=2, anchor="midleft")
            left = pygame.Rect(x + CTRL_X, y - BTN_H // 2, BTN_W, BTN_H)
            right = pygame.Rect(left.right + VALUE_W, left.y, BTN_W, BTN_H)
            self._button(surf, left, "<", lambda c=change: c(-1), size=34)
            self._button(surf, right, ">", lambda c=change: c(1), size=34)
            value_rect = pygame.Rect(left.right, left.y, VALUE_W, BTN_H)
            value = ui.text_fit(str(read()), ui.LABEL_BOLD, 22, TITLE, VALUE_W - 12, tracking=2)
            surf.blit(value, value.get_rect(center=value_rect.center))
            if label.startswith("SOUND"):
                self.buttons.append((value_rect, lambda: self.ctx.chimes.preview(self.draft["chime"]["sound"])))

        self._button(surf, pygame.Rect(PANEL.centerx - 340, PANEL.bottom - 80, 200, 58), "CANCEL", self.cancel)
        self._button(surf, pygame.Rect(PANEL.centerx - 100, PANEL.bottom - 80, 200, 58), "SAVE", self.save,
                     colour=TITLE)
        self._button(surf, pygame.Rect(PANEL.right - 260, PANEL.bottom - 80, 200, 58), "EXIT CLOCK", self.on_exit,
                     size=26, colour=(240, 120, 100))
