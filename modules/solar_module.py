# Solar Module
# Description: This module calculates solar position and sunrise/sunset times using the pysolar library and an external API.

import requests
import threading
import time
from datetime import datetime, timezone, timedelta
from pysolar.solar import get_altitude, get_azimuth

class SolarCalculator:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        self.latitude = latitude
        self.longitude = longitude
        self.sun_api_url = "https://api.sunrise-sunset.org/json"
        self.local_tz = timezone(timedelta(hours=-5))  # EST

        self.sun_times = {
            "sunrise": "--",
            "sunset": "--",
            "solar_noon": "--"
        }

        self.solar_position = {
            "solar_alt": "--",
            "solar_az": "--",
            "sun_time": "--"
        }

        self.update_sun_times()

    def update_sun_times(self):
        try:
            res = requests.get(self.sun_api_url, params={
                "lat": self.latitude,
                "lng": self.longitude,
                "formatted": 0
            }, timeout=5).json()["results"]

            self.sun_times.update({
                key: datetime.fromisoformat(res[key])
                    .replace(tzinfo=timezone.utc)
                    .astimezone(self.local_tz)
                    .strftime("%H:%M")
                for key in ["sunrise", "sunset", "solar_noon"]
            })
        except Exception as e:
            print(f"[Solar] Error fetching sun times: {e}")

    def update_solar_position(self):
        try:
            now = datetime.now(timezone.utc)
            alt = get_altitude(self.latitude, self.longitude, now)
            az = get_azimuth(self.latitude, self.longitude, now)

            self.solar_position.update({
                "solar_alt": round(alt, 2) if alt > 0 else "Below Horizon",
                "solar_az": round(az, 2),
                "sun_time": datetime.now().strftime("%m-%d %H:%M:%S")
            })
        except Exception as e:
            print(f"[Solar] Error calculating position: {e}")

    def get_data(self):
        return {**self.sun_times, **self.solar_position}

    def start_monitor(self, socketio, interval=20):
        def loop():
            while True:
                self.update_solar_position()
                socketio.emit("solar_update", self.get_data())
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()