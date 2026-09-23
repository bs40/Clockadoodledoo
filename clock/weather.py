"""Current conditions from Open-Meteo (free, no API key), fetched on a background thread."""
import json
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime

URL = "https://api.open-meteo.com/v1/forecast"
REFRESH_S = 15 * 60
RETRY_S = 60

_COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

# WMO weather code -> (description, icon name)
_CODES = {
    0: ("CLEAR", "sun"), 1: ("MAINLY CLEAR", "sun"), 2: ("PARTLY CLOUDY", "partly"),
    3: ("OVERCAST", "cloud"), 45: ("FOG", "fog"), 48: ("FREEZING FOG", "fog"),
    51: ("LIGHT DRIZZLE", "rain"), 53: ("DRIZZLE", "rain"), 55: ("HEAVY DRIZZLE", "rain"),
    56: ("FREEZING DRIZZLE", "rain"), 57: ("FREEZING DRIZZLE", "rain"),
    61: ("LIGHT RAIN", "rain"), 63: ("RAIN", "rain"), 65: ("HEAVY RAIN", "rain"),
    66: ("FREEZING RAIN", "rain"), 67: ("FREEZING RAIN", "rain"),
    71: ("LIGHT SNOW", "snow"), 73: ("SNOW", "snow"), 75: ("HEAVY SNOW", "snow"),
    77: ("SNOW GRAINS", "snow"), 80: ("LIGHT SHOWERS", "rain"), 81: ("SHOWERS", "rain"),
    82: ("HEAVY SHOWERS", "rain"), 85: ("SNOW SHOWERS", "snow"), 86: ("SNOW SHOWERS", "snow"),
    95: ("THUNDERSTORM", "storm"), 96: ("THUNDERSTORM", "storm"), 99: ("THUNDERSTORM", "storm"),
}

DEMO = {
    "temp": 16, "humidity": 68, "pressure": 1016, "wind": 12, "wind_dir": "SW",
    "summary": "CLEAR", "icon": "sun", "temp_unit": "°C", "wind_unit": "mph",
    "sun_events": [],
}


class Weather:
    def __init__(self, config, demo=False):
        self.config = config
        self.current = dict(DEMO) if demo else None
        self.version = 0
        self._demo = demo

    def start(self):
        if not self._demo:
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            time.sleep(REFRESH_S if self.fetch_once() else RETRY_S)

    def fetch_once(self):
        if self._demo:
            return True
        loc, units = self.config["location"], self.config["units"]
        query = urllib.parse.urlencode({
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,pressure_msl,"
                       "wind_speed_10m,wind_direction_10m,weather_code",
            "daily": "sunrise,sunset", "forecast_days": 2, "timezone": "auto",
            "temperature_unit": units["temperature"], "wind_speed_unit": units["wind"],
        })
        try:
            with urllib.request.urlopen(f"{URL}?{query}", timeout=10) as resp:
                data = json.load(resp)
            cur = data["current"]
            summary, icon = _CODES.get(cur["weather_code"], ("", "cloud"))
            events = [(datetime.fromisoformat(t), kind)
                      for kind in ("sunrise", "sunset") for t in data["daily"][kind]]
            self.current = {
                "temp": round(cur["temperature_2m"]),
                "humidity": round(cur["relative_humidity_2m"]),
                "pressure": round(cur["pressure_msl"]),
                "wind": round(cur["wind_speed_10m"]),
                "wind_dir": _COMPASS[int((cur["wind_direction_10m"] + 22.5) // 45) % 8],
                "summary": summary, "icon": icon,
                "temp_unit": "°F" if units["temperature"] == "fahrenheit" else "°C",
                "wind_unit": {"kmh": "km/h", "ms": "m/s", "kn": "kn"}.get(units["wind"], units["wind"]),
                "sun_events": sorted(events),
            }
            self.version += 1
            return True
        except (OSError, ValueError, KeyError) as exc:
            print(f"weather: fetch failed: {exc}")
            return False

    def next_sun_event(self, now):
        """Next (time, 'sunrise'|'sunset') after `now` (naive local time), or None."""
        for when, kind in (self.current or {}).get("sun_events", []):
            if when > now:
                return when, kind
        return None
