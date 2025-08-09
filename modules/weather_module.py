# Weather Module 
# Open-Meteo with config-driven profiles

import requests
import time
from datetime import datetime
from utilities import config  # <- read GEO_* and LOCATION_PROFILES

WEATHERCODE_MAP = {
    0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Heavy Rain",
    71: "Snow", 73: "Snow", 75: "Heavy Snow",
    80: "Showers", 81: "Showers", 82: "Heavy Showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Severe Tstorm"
}

def _resolve_profile(profile_name: str):
    """Return (lat, lon, elev, tz, name) from config.LOCATION_PROFILES, with sane fallbacks."""
    profiles = getattr(config, "LOCATION_PROFILES", {})
    raw = profiles.get(profile_name)
    if isinstance(raw, dict):
        lat = raw.get("lat", config.GEO_LAT)
        lon = raw.get("lon", config.GEO_LON)
        elev = raw.get("elev", config.GEO_ELEV)
        tz = raw.get("tz", "UTC")
    elif isinstance(raw, (tuple, list)) and len(raw) >= 3:
        lat, lon, elev = raw[:3]
        # best-effort TZ if tuples used
        tz = "America/New_York" if "chapel" in profile_name else "America/Chicago"
    else:
        lat, lon, elev, tz = config.GEO_LAT, config.GEO_LON, config.GEO_ELEV, "America/New_York"
    return float(lat), float(lon), float(elev), tz, profile_name

class WeatherForecast:
    def __init__(self, profile="chapel_hill"):
        lat, lon, elev, tz, name = _resolve_profile(profile)
        self.latitude = lat
        self.longitude = lon
        self.elevation = elev
        self.tz = tz
        self.profile = name
        self._build_url()

        self.last_success = None
        self.weather_data = {
            "temperature": "--",
            "wind_speed": "--",
            "sky_conditions": "Unknown",
            "precip_chance": "--",
            "last_checked": "--",
            "location_profile": self.profile,
        }

    # ---- public API ----
    def use_profile(self, profile_name: str):
        """Switch to a config profile (KC/CH/etc) and rebuild URL."""
        lat, lon, elev, tz, name = _resolve_profile(profile_name)
        self.latitude, self.longitude, self.elevation, self.tz, self.profile = lat, lon, elev, tz, name
        self._build_url()

    def refresh_now(self, socketio=None):
        self.check_weather()
        if socketio:
            socketio.emit("update_weather", self.weather_data)

    def get_data(self):
        return self.weather_data

    def start_monitor(self, socketio, interval=600):
        def loop():
            self.refresh_now(socketio)
            while True:
                time.sleep(interval)
                self.refresh_now(socketio)
        socketio.start_background_task(loop)

    # ---- internals ----
    def _build_url(self):
        base = "https://api.open-meteo.com/v1/forecast"
        self.api_url = (
            f"{base}?latitude={self.latitude}&longitude={self.longitude}"
            f"&current_weather=true"
            f"&hourly=precipitation_probability"
            f"&forecast_days=1"
            f"&timezone={self.tz}"
        )

    def check_weather(self, retries=3, timeout=3):
        delay = 0.75
        last_err = None
        for _ in range(max(1, retries)):
            try:
                res = requests.get(self.api_url, timeout=timeout)
                res.raise_for_status()
                body = res.json()

                cur = body.get("current_weather", {})
                precip_series = body.get("hourly", {}).get("precipitation_probability", [])
                precip = precip_series[0] if precip_series else "--"
                code = cur.get("weathercode", None)
                sky = WEATHERCODE_MAP.get(code, "Unknown") if code is not None else "Unknown"

                self.last_success = datetime.now()
                self.weather_data = {
                    "temperature": round(cur.get("temperature", 0), 1) if "temperature" in cur else "--",
                    "wind_speed": cur.get("windspeed", "--"),
                    "sky_conditions": sky,
                    "precip_chance": int(round(precip)) if isinstance(precip, (int, float)) else "--",
                    "last_checked": self.last_success.strftime("%m-%d %H:%M:%S"),
                    "location_profile": self.profile,
                }
                return
            except Exception as e:
                last_err = e
                time.sleep(delay)
                delay *= 1.6  # backoff
        # keep old values, just stamp time
        self.weather_data.update({"last_checked": datetime.now().strftime("%m-%d %H:%M:%S")})
        print(f"[Weatherman] Error fetching weather ({self.profile}): {last_err}")