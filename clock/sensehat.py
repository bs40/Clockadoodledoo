"""Raspberry Pi Sense HAT: room temperature, humidity and pressure, and which way up the clock is.

Runs on a background thread. Where the Sense HAT library or the HAT itself is missing (the
development PC, a Pi without one) `available` is False and everything reads None.

The HAT's thermometer sits over the Pi's CPU and reads high, so the temperature is
compensated with the CPU temperature (the usual sense-hat formula) and then offset by the
user's `temp_trim` from the settings panel.
"""
import threading
import time

CPU_TEMP = "/sys/class/thermal/thermal_zone0/temp"
CPU_FACTOR = 5.466          # temp - (cpu - temp) / CPU_FACTOR
SMOOTH = 0.25               # exponential smoothing of the readings
INTERVAL = 2.0              # seconds between sensor reads
TILT = 0.6                  # g along an axis before the clock counts as turned that way
STEADY = 4                  # consecutive agreeing tilt readings before the orientation changes

DEMO = {"temp": 21.4, "humidity": 45, "pressure": 1013}


class Sense:
    def __init__(self, config, demo=False):
        self.config = config
        self.available = False
        self.room = dict(DEMO) if demo else None      # {"temp", "humidity", "pressure"} or None
        self.version = 0                              # bumps when the rounded readings change
        self.orientation = None                       # "landscape", "portrait", ... from the accelerometer
        self._hat = None
        self._smooth = {}
        self._tilt_votes = []
        if not demo:
            threading.Thread(target=self._run, daemon=True).start()

    @property
    def cfg(self):
        return self.config.setdefault("sense", {})

    # ---- background thread -----------------------------------------------------------
    def _run(self):
        try:
            from sense_hat import SenseHat
            self._hat = SenseHat()
            self._hat.clear()                          # LEDs off; we only want the sensors
            self.available = True
        except Exception as exc:                       # library missing, or no HAT on the header
            print(f"sense hat: not available ({exc.__class__.__name__}: {exc})")
            return
        next_read = 0.0
        while True:
            now = time.monotonic()
            if now >= next_read:
                next_read = now + INTERVAL
                try:
                    self._read_environment()
                except Exception as exc:
                    print(f"sense hat: read failed: {exc}")
            try:
                self._read_tilt()
            except Exception as exc:
                print(f"sense hat: accelerometer failed: {exc}")
            time.sleep(0.5)

    def _read_environment(self):
        hat = self._hat
        temp = hat.get_temperature_from_humidity()
        humidity = hat.get_humidity()
        pressure = hat.get_pressure()
        if pressure <= 0:                              # the first read after power-up comes back as 0
            pressure = hat.get_pressure()
        try:
            with open(CPU_TEMP) as fh:
                cpu = int(fh.read()) / 1000
            temp = temp - (cpu - temp) / CPU_FACTOR
        except OSError:
            pass
        temp += float(self.cfg.get("temp_trim", 0.0))
        raw = {"temp": temp, "humidity": humidity, "pressure": pressure if pressure > 0 else None}
        for key, value in raw.items():
            if value is None:
                continue
            old = self._smooth.get(key)
            self._smooth[key] = value if old is None else old + (value - old) * SMOOTH
        if "pressure" not in self._smooth:
            return
        room = {"temp": round(self._smooth["temp"], 1), "humidity": round(self._smooth["humidity"]),
                "pressure": round(self._smooth["pressure"])}
        if room != self.room:
            self.room = room
            self.version += 1

    def _read_tilt(self):
        g = self._hat.get_accelerometer_raw()
        x, y = g["x"], g["y"]
        if abs(y) >= TILT and abs(y) >= abs(x):
            tilt = "landscape" if y < 0 else "landscape-flipped"
        elif abs(x) >= TILT:
            tilt = "portrait" if x > 0 else "portrait-flipped"
        else:
            return                                     # lying flat or in between: keep what we have
        if self.cfg.get("swap_portrait") and tilt.startswith("portrait"):
            tilt = "portrait-flipped" if tilt == "portrait" else "portrait"
        self._tilt_votes = (self._tilt_votes + [tilt])[-STEADY:]
        if len(self._tilt_votes) == STEADY and len(set(self._tilt_votes)) == 1:
            self.orientation = tilt


def merged(outdoor, room):
    """The readings a face shows: the weather service's values, with humidity and pressure from
    the room sensors when they exist, plus the room temperature."""
    if outdoor is None and room is None:
        return None
    readings = dict(outdoor or {})
    if room:
        readings["room_temp"] = room["temp"]
        readings["humidity"] = room["humidity"]
        readings["pressure"] = room["pressure"]
    return readings
