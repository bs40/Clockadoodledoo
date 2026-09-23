# Clockadoodledoo

Animated clock faces for a Raspberry Pi 4 driving a Waveshare 10.4" 1600x720 touch screen.
Python + pygame-ce; the same code runs in a window on a PC for development.

## Run on the PC

    .venv\Scripts\python.exe run.py                 # live time and weather, 1600x720 window
    .venv\Scripts\python.exe run.py --scale 0.75    # smaller window
    .venv\Scripts\python.exe run.py --demo --time 2026-09-23T19:42:17   # mockup values, no network

    .venv\Scripts\python.exe run.py --face cosmonaut                    # start on a particular face

Tap, click or Space switches to the next face. Esc or Q quits.
`--screenshot out.png` renders one frame and exits. On the Pi, add `--fullscreen`.

## Faces

- `orrery` - drawn entirely in code.
- `cosmonaut` - poster artwork from `retface4.png`. `tools\prep_cosmonaut.py` paints out the
  poster's baked-in date, time and weather and writes `assets/faces/cosmonaut/background.png`;
  re-run it if the artwork changes. The face then draws the live readouts on top.
  Animation: she blinks every 16-24 s and twice on each five-minute mark, the colon shows on
  odd seconds, stars twinkle slowly and the rocket's smoke ripples. Timings and the eyelid and
  plume positions are constants at the top of `clock/faces/cosmonaut.py`; the positions are in
  `background.png` pixels, so they need re-measuring if the artwork changes.
- `orbit` - console artwork from `retface2.png`, prepared by `tools\prep_orbit.py`. Hours, minutes
  and seconds are split-flap cards that flip when they change; a satellite laps the globe once a
  minute (far right on :00) and passes behind it; the cross-hair markers pulse. Panel, globe and
  orbit positions are constants at the top of `clock/faces/orbit.py`, in `retface2.png` pixels.
- `saturn` - poster artwork from `retface3.png`, prepared by `toolsprep_saturn.py`. Twinkling stars,
  blinking colon and an occasional meteor across the sky.

`tools\poster.py` holds the shared paint-out and letterbox steps the prep scripts use.

## Layout

- `config.json` - face, location (for weather), units, 12/24 hour, frame rate
- `clock/app.py` - main loop
- `clock/faces/` - one module per face; register new ones in `faces/__init__.py`
- `clock/weather.py` - Open-Meteo current conditions + sunrise/sunset, refreshed every 15 min
- `clock/astro.py` - moon phase
- `clock/ui.py`, `clock/icons.py` - palette, fonts, tracked text, vector icons
- `assets/fonts/` - Michroma, Barlow Condensed, Anton and Russo One (SIL OFL, licences alongside)
- `assets/sounds/` - chime files (not used yet)

Faces draw at a fixed 1600x720; the app scales that to whatever window or screen it gets.

## Putting it on the Pi

1. Flash Raspberry Pi OS (64-bit, with desktop) with Raspberry Pi Imager. In its settings set the
   hostname to `clock`, a username and password, your Wi-Fi, and enable SSH.
2. Boot the Pi with the screen attached, then from this folder on the PC:  `deploy user@clock.local`
3. On the Pi (over SSH or a keyboard):  `bash ~/clock/pi/install.sh`  then  `sudo reboot`

`deploy.cmd` copies the project over SSH; run it again after any change. `pi/install.sh` creates the
Pi's virtual environment, installs the requirements, autostarts the clock full screen at login and
turns off screen blanking. Tap the screen to change face; a keyboard's Esc quits to the desktop.

## Chimes

`config.json` → `chime`: `sound` is a file name in `assets/sounds` without its extension
(`run.py --chime list` prints them), `half_hour` adds a chime at :30, `volume` is 0-1, and
nothing plays between `quiet_from` and `quiet_to`. `run.py --chime` plays the configured chime
and exits; `run.py --chime ping` plays a named one. `assets/sounds/LICENCES.txt` says where each
sound came from (all CC0); `tools\make_sounds.py` regenerates the synthesised ones.

## Settings panel and brightness

Press and hold anywhere on the clock (or press S on a keyboard) to open the settings panel:
chime sound (tap the name to hear it), when to chime, volume, quiet hours, default face, day and
night brightness with the dimming hours, and 12/24-hour clock. Save writes `config.json`, which is
never overwritten by `deploy`; `config.default.json` holds the defaults for anything not in it.

Brightness is set through the screen's DDC/CI channel with `ddcutil` (installed by `pi/install.sh`).
Where ddcutil isn't available, such as on the PC, the picture is dimmed in software instead.

## Automatic updates

The Pi keeps `~/clock` as a git checkout of the GitHub repository. A systemd user timer runs
`pi/update.sh` every 5 minutes: if `origin/main` has moved it resets the checkout to it, installs
any new requirements and leaves an `.update-pending` note. The clock restarts itself into the new
code during the dim hours (or after 30 hours, whichever is first), never while the settings panel
is open. `config.json` is untracked, so settings survive updates.

Set it up once with `bash ~/clock/pi/enable-updates.sh REPO_URL` on the Pi. After that,
publishing a change is a `git push`. `deploy` still works for pushing straight to the Pi
without going through GitHub, but the next update check will replace whatever it copied.
The source mockup PNGs (`retface*.png`) are not committed; only the prepared backgrounds are.

Repository: https://github.com/bs40/Clockadoodledoo (private). Publish a change with `git push`; the Pi picks it up within 5 minutes.
