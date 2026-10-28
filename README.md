# Clockadoodledoo

Animated clock faces for a Raspberry Pi 4 driving a Waveshare 10.4" 1600x720 touch screen.
Python + pygame-ce; the same code runs in a window on a PC for development.

## Run on the PC

    .venv\Scripts\python.exe run.py                 # live time and weather, 1600x720 window
    .venv\Scripts\python.exe run.py --scale 0.75    # smaller window
    .venv\Scripts\python.exe run.py --demo --time 2026-09-23T19:42:17   # mockup values, no network

    .venv\Scripts\python.exe run.py --face cosmonaut                    # start on a particular face

    .venv\Scripts\python.exe run.py --portrait                         # the portrait layouts

Tap, click or Space switches to the next face. Esc or Q quits.
`--screenshot out.png` renders one frame and exits. On the Pi, add `--fullscreen`.

## Sense HAT

With a Raspberry Pi Sense HAT fitted (`pi/install.sh` installs the `sense-hat` package and
makes the venv able to see it), `clock/sensehat.py` reads it on a background thread:

- room temperature, humidity and pressure. Every face shows the room temperature, and its
  HUMIDITY and PRESSURE readouts switch from the weather service to the sensors. The HAT's
  thermometer sits over the CPU and reads high, so the temperature is compensated with the CPU
  temperature and then offset by the panel's ROOM TEMP TRIM (set it against a real thermometer).
- which way up the clock is, from the accelerometer. With ORIENTATION set to AUTO (SENSE HAT),
  turning the clock switches it between landscape and portrait by itself, a couple of seconds
  after it settles. If the two portrait directions come out reversed, set `sense.swap_portrait`
  to true in `config.json`.

Without a HAT nothing changes: readings come from the weather service and AUTO means landscape.

## Orientation

Every face has a landscape (1600x720) and a portrait (720x1600) layout. The settings panel's
ORIENTATION row picks AUTO (SENSE HAT), LANDSCAPE, PORTRAIT, PORTRAIT FLIPPED or LANDSCAPE
FLIPPED; the clock draws the portrait
canvas and turns it onto the screen itself (touch positions are turned to match), so the
screen can simply be stood on its end with no operating-system changes. PORTRAIT puts the top
of the picture at the screen's left edge; if it comes up upside down, choose PORTRAIT FLIPPED.
In a window on the PC the picture is shown upright; `--rotate` shows it turned as the Pi does.

Portrait backgrounds for the artwork faces are composed from pieces of the mockups by the same
`tools\prep_*.py` scripts (`assets/faces/<face>/portrait.png`); each face module has a
`LAYOUTS` table with the positions for both orientations.

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
- `saturn` - poster artwork from `retface3.png`, prepared by `tools\prep_saturn.py`. Twinkling stars,
  blinking colon and an occasional meteor across the sky.
- `pixel` - pixel-art city from `pixface1.png`, prepared by `tools\prep_pixel.py`. Rain falls over
  the city, the neon sign and lantern flicker, the pixel weather icon animates, the colon blinks.
- `launch` - rocket climbing past the Earth, from `face designs/retro_space_clock_01_rocket_launch.png`,
  prepared by `tools\prep_launch.py`. The exhaust flickers, the lens-flare star and faint stars
  twinkle, the launch tower's beacons blink, the colon blinks.
- `astronaut` - astronaut in a bubble helmet beside a ringed planet (`..._02_astronaut.png`,
  `tools\prep_astronaut.py`). She blinks now and then, a glint sweeps across her helmet every
  half minute or so, the city's windows glow and its spires' beacons blink, stars twinkle.
- `control` - control room looking out at the Earth (`..._03_control_room.png`, `tools\prep_control.py`).
  The right-hand column is a small live story: altitude and velocity drift over each 92-minute
  orbit and NEXT ORBIT counts down to the next one. Console screens pulse, lamps blink, the radar
  scope sweeps, the sparkle star and window stars twinkle, an occasional meteor.
- `colony` - robot overlooking a Mars colony (`..._04_robot_colony.png`, `tools\prep_colony.py`).
  The robot's eyes glow and dim, its antenna and the colony's tower lamps blink, the dome's
  windows glow, stars twinkle, an occasional meteor.
- `station` - rocket ship passing a wheel station (`..._05_orbital_station.png`, `tools\prep_station.py`).
  The engine flames flicker and waver, beacons blink on the ship and the station, stars twinkle,
  an occasional meteor. The VISIBLE TONIGHT panel is part of the artwork.
- `explorer` - astronaut on a red canyon world (`..._06_distant_world.png`, `tools\prep_explorer.py`).
  He blinks now and then, the star on his visor twinkles and a glint sweeps across it, the
  spaceplane's beacon and strobe blink, stars twinkle, an occasional meteor.
- `rainbow` - rainbow valley (`face designs/psychedelic_clock_01_rainbow_valley.png`, `tools\prep_rainbow.py`).
  The sun's glow breathes, a ring of light passes out across the rainbow now and then, stars
  and sparkles twinkle, an occasional shooting star.
- `vision` - cosmic vision (`..._02_cosmic_vision.png`, `tools\prep_vision.py`). The third-eye
  starburst brightens and fades like breathing, the orbs down the tunnel of faces light up one
  after another, the sparkle stars twinkle.
- `tunnel` - flower tunnel (`..._03_flower_tunnel.png`, `tools\prep_tunnel.py`). The light at the
  end breathes, the golden path on the water shimmers, specks of light drift out of the tunnel
  and now and then a soft arch of light travels out through the flowers.
- `rings` - ringed planet over a lake (`..._04_ringed_planet.png`, `tools\prep_rings.py`). The
  lake shimmers, the moons glow, stars twinkle, an occasional shooting star.
- `mandala` - meditation (`..._05_mandala_meditation.png`, `tools\prep_mandala.py`). One slow
  breath every 7 s: light rises up the chakras to the crown, the mandala brightens, a ripple
  spreads from the figure; the lotuses glow, stars twinkle.
- `spiral` - flower spiral (`face designs/Psychedelic_Clock_06.png`, `tools\prep_spiral.py`). The
  spiral turns slowly inward (one turn every 80 s), its centre glows, bokeh lights pulse. Built
  from a small 755x332 copy of the design; for a sharper picture put a full-size copy in
  `face designs` and change `SRC` in the prep script (and `POSTER_H` in `clock/faces/spiral.py`
  if its proportions differ).

The retro-space and psychedelic faces (`launch` onwards) share `clock/faces/artwork.py`: the live readout
layer (date, time, weather rows) and small animation pieces (twinkling stars, sparkles, meteors,
flicker, blinking lamps, a visor glint). Their `LAYOUTS` positions are in mockup pixels with the
mockup scaled to 2000 px wide, which is also how their prep scripts measure.

`tools\poster.py` holds the shared paint-out, re-texturing and letterbox steps the prep scripts use.

## Layout

- `config.json` - face, orientation, location (for weather), units, 12/24 hour, frame rate
- `clock/app.py` - main loop
- `clock/faces/` - one module per face; register new ones in `faces/__init__.py`
- `clock/weather.py` - Open-Meteo current conditions + sunrise/sunset, refreshed every 15 min
- `clock/sensehat.py` - Sense HAT room readings and tilt (see Sense HAT below)
- `clock/astro.py` - moon phase
- `clock/ui.py`, `clock/icons.py` - palette, fonts, tracked text, vector icons
- `assets/fonts/` - Michroma, Barlow Condensed, Anton, Russo One, Press Start 2P, Silkscreen, Fraunces and Jost (SIL OFL, licences alongside)
- `assets/sounds/` - chime files (see Chimes below)

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
The source mockup PNGs (`retface*.png`, `pixface*.png` and the `face designs` folder) are not committed;
only the prepared backgrounds are.

Repository: https://github.com/bs40/Clockadoodledoo. Publish a change with `git push`; the Pi picks it up within 5 minutes.
