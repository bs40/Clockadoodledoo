"""Touch settings panel, opened by press-and-hold.

Edits a draft copy of the config; Save writes config.json and applies the changes, Cancel
throws the draft away. The face carries on animating behind the panel. The panel lays itself
out in two columns on a landscape canvas and one column on a portrait one.
"""
import copy
import json

import pygame

from . import ui
from .chimes import available
from .schedule import step_hhmm

BTN_W, BTN_H = 62, 54          # the < > buttons
VALUE_W = 226
SECTIONS = ("CLOCK, CHIME & SENSOR", "DISPLAY")
ORIENTATIONS = ("auto", "landscape", "portrait", "portrait-flipped", "landscape-flipped")

BG = (9, 19, 27)
BORDER = (122, 214, 228)
BUTTON = (24, 50, 62)
BUTTON_HI = (38, 84, 102)
TITLE = (250, 186, 92)
TEXT = ui.CREAM
DIM = ui.MUTED


def _pct(v):
    return f"{round(v * 100)}%"


def _layout(size):
    """Panel geometry for a canvas of this size."""
    w, h = size
    if w >= h:                                          # landscape: two columns side by side
        return dict(panel=pygame.Rect(110, 50, w - 220, h - 100), cols=(150, 830), col_w=620,
                    row0=172, row_h=58, ctrl_x=290, stacked=False,
                    buttons=((w // 2 - 340, 200), (w // 2 - 100, 200), (w - 370, 200)))
    return dict(panel=pygame.Rect(24, 40, w - 48, 1190), cols=(56, 56), col_w=w - 112,
                row0=176, row_h=60, ctrl_x=250, stacked=True,
                buttons=((36, 200), (260, 200), (484, 200)))


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
        self.layout = None
        self.rows = self._rows()

    # ---- the rows, as (section, label, read, change) -----------------------------
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

        def orientation():
            cur = d()["display"].get("orientation", "auto")
            return "AUTO (SENSE HAT)" if cur == "auto" else cur.replace("-", " ").upper()

        def orientation_change(k):
            cur = d()["display"].get("orientation", "auto")
            d()["display"]["orientation"] = ORIENTATIONS[(ORIENTATIONS.index(cur) + k) % len(ORIENTATIONS)]

        def trim():
            return f"{d().setdefault('sense', {}).get('temp_trim', 0.0):+.1f}\u00b0"

        def trim_change(k):
            sense = d().setdefault("sense", {})
            sense["temp_trim"] = round(min(max(sense.get("temp_trim", 0.0) + k * 0.5, -10.0), 10.0), 1)

        return [
            (0, "SOUND", *spin_choice("chime", "sound", available)),
            (0, "CHIME", when, change_when),
            (0, "VOLUME", *spin_num("chime", "volume", 0.0, 1.0, 0.1, _pct)),
            (0, "QUIET FROM", *spin_time("chime", "quiet_from")),
            (0, "QUIET UNTIL", *spin_time("chime", "quiet_to")),
            (0, "CLOCK", lambda: "24 HOUR" if d()["clock"]["24_hour"] else "12 HOUR", clock_change),
            (0, "ROOM TEMP TRIM", trim, trim_change),
            (1, "FACE", lambda: d()["face"].upper(), face_change),
            (1, "ORIENTATION", orientation, orientation_change),
            (1, "DAY BRIGHTNESS", *spin_num("display", "day", 10, 100, 10, lambda v: f"{v}%")),
            (1, "NIGHT BRIGHTNESS", *spin_num("display", "night", 0, 100, 10, lambda v: f"{v}%")),
            (1, "DIM FROM", *spin_time("display", "dim_from")),
            (1, "DIM UNTIL", *spin_time("display", "dim_to")),
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
        for key, value in self.draft.items():          # update in place: other modules hold these dicts
            if isinstance(value, dict) and isinstance(self.ctx.config.get(key), dict):
                self.ctx.config[key].clear()
                self.ctx.config[key].update(value)
            else:
                self.ctx.config[key] = value
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
        return bool(self.layout) and self.layout["panel"].collidepoint(pos)

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
        L = self.layout = _layout(surf.get_size())
        panel_rect = L["panel"]
        self.buttons = []
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((*BG, 236))
        surf.blit(panel, panel_rect.topleft)
        pygame.draw.rect(surf, BORDER, panel_rect, 3, border_radius=18)
        ui.blit_text(surf, "SETTINGS", ui.LABEL_BOLD, 40, TITLE, (panel_rect.centerx, panel_rect.y + 42),
                     tracking=10, anchor="center")
        hint = "press and hold the clock to open this panel  -  tap a sound name to hear it"
        if L["stacked"]:
            hint = "hold the clock to open  -  tap a sound name to hear it"
        ui.blit_text(surf, hint, ui.LABEL, 22, DIM, (panel_rect.centerx, panel_rect.y + 78), tracking=2, anchor="center")

        y = L["row0"]
        rows_by_section = [[r for r in self.rows if r[0] == s] for s in range(len(SECTIONS))]
        for s, title in enumerate(SECTIONS):
            x = L["cols"][s]
            top = y if L["stacked"] else L["row0"]
            ui.blit_text(surf, title, ui.LABEL_MED, 24, BORDER, (x, top - 36), tracking=8)
            pygame.draw.line(surf, BORDER, (x, top - 8), (x + L["col_w"], top - 8), 1)
            for i, (_, label, read, change) in enumerate(rows_by_section[s]):
                cy = top + i * L["row_h"] + L["row_h"] // 2
                ui.blit_text(surf, label, ui.LABEL_MED, 27, TEXT, (x, cy), tracking=2, anchor="midleft")
                left = pygame.Rect(x + L["ctrl_x"], cy - BTN_H // 2, BTN_W, BTN_H)
                right = pygame.Rect(left.right + VALUE_W, left.y, BTN_W, BTN_H)
                self._button(surf, left, "<", lambda c=change: c(-1), size=34)
                self._button(surf, right, ">", lambda c=change: c(1), size=34)
                value_rect = pygame.Rect(left.right, left.y, VALUE_W, BTN_H)
                value = ui.text_fit(str(read()), ui.LABEL_BOLD, 22, TITLE, VALUE_W - 12, tracking=2)
                surf.blit(value, value.get_rect(center=value_rect.center))
                if label == "SOUND":
                    self.buttons.append((value_rect, lambda: self.ctx.chimes.preview(self.draft["chime"]["sound"])))
            if L["stacked"]:
                y = top + len(rows_by_section[s]) * L["row_h"] + 60

        (cx, cw), (sx, sw), (ex, ew) = L["buttons"]
        by = panel_rect.bottom - 80
        self._button(surf, pygame.Rect(cx, by, cw, 58), "CANCEL", self.cancel)
        self._button(surf, pygame.Rect(sx, by, sw, 58), "SAVE", self.save, colour=TITLE)
        self._button(surf, pygame.Rect(ex, by, ew, 58), "EXIT CLOCK", self.on_exit, size=26, colour=(240, 120, 100))
