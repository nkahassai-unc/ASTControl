import requests
from pysolar.solar import get_altitude, get_azimuth
from datetime import datetime, timezone, timedelta

class SolarCalculator:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        self.latitude = latitude
        self.longitude = longitude
        self.sun_times = {"sunrise": "--", "sunset": "--", "solar_noon": "--", "last_updated": None}
        self.sun_times_api_url = "https://api.sunrise-sunset.org/json"
        self.solar_position = {"altitude": "--", "azimuth": "--", "time": None}
        self.update_sun_times()  # Initialize with sunrise/sunset data

    def update_sun_times(self):
        """Fetch sunrise, sunset, and solar noon times once every 12 hours."""
        try:
            response = requests.get(self.sun_times_api_url, params={"lat": self.latitude, "lng": self.longitude, "formatted": 0})
            response.raise_for_status()
            results = response.json().get("results", {})
            self.sun_times.update({
                "sunrise": self._convert_utc_to_est(results["sunrise"]),
                "sunset": self._convert_utc_to_est(results["sunset"]),
                "solar_noon": self._convert_utc_to_est(results["solar_noon"]),
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
        except requests.RequestException as e:
            print(f"Error fetching sunrise/sunset data: {e}")

    def update_solar_position(self):
        """Update solar altitude and azimuth every 20 seconds."""
        now = datetime.now(timezone.utc)
        altitude = get_altitude(self.latitude, self.longitude, now)
        azimuth = get_azimuth(self.latitude, self.longitude, now)
        self.solar_position.update({
            "altitude": round(altitude, 2) if altitude > 0 else "Below Horizon",
            "azimuth": round(azimuth, 2),
            "time": self._convert_utc_to_est(now.strftime("%Y-%m-%d %H:%M:%S"))
        })

    def get_all_data(self):
        """Combine solar position with sunrise/sunset times."""
        return {**self.sun_times, **self.solar_position}

    @staticmethod
    def _convert_utc_to_est(utc_time_str):
        """Convert UTC to EST."""
        try:
            utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
            est_time = utc_time - timedelta(hours=5)
            return est_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return utc_time_str
