import requests
from pysolar.solar import get_altitude, get_azimuth
from datetime import datetime, timezone, timedelta

class SolarCalculator:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        self.latitude = latitude
        self.longitude = longitude
        self.sun_times = {"sunrise": "--", "sunset": "--", "solar_noon": "--"}
        self.sun_times_api_url = "https://api.sunrise-sunset.org/json"
        self.solar_position = {"solar_alt": "--", "solar_az": "--", "sun_time": None}
        self.update_sun_times()  # Initialize with sunrise/sunset data
        
    def update_sun_times(self):
        """Fetch sunrise, sunset, and solar noon times once every 12 hours."""
        try:
            response = requests.get(self.sun_times_api_url, params={"lat": self.latitude, "lng": self.longitude, "formatted": 0})
            response.raise_for_status()
            results = response.json().get("results", {})
            self.sun_times.update({
                "sunrise": datetime.fromisoformat(results["sunrise"])
                        .replace(tzinfo=timezone.utc)
                        .astimezone(timezone(timedelta(hours=-5)))
                        .strftime("%H:%M"),
                "sunset": datetime.fromisoformat(results["sunset"])
                        .replace(tzinfo=timezone.utc)
                        .astimezone(timezone(timedelta(hours=-5)))
                        .strftime("%H:%M"),
                "solar_noon": datetime.fromisoformat(results["solar_noon"])
                            .replace(tzinfo=timezone.utc)
                            .astimezone(timezone(timedelta(hours=-5)))
                            .strftime("%H:%M"),
            })
        except requests.RequestException as e:
            print(f"Error fetching sunrise/sunset data: {e}")

    def update_solar_position(self):
        """Update solar altitude and azimuth every 20 seconds."""
        now = datetime.now(timezone.utc)
        altitude = get_altitude(self.latitude, self.longitude, now)
        azimuth = get_azimuth(self.latitude, self.longitude, now)
        self.solar_position.update({
            "solar_alt": round(altitude, 2) if altitude > 0 else "Below Horizon",
            "solar_az": round(azimuth, 2),
            "sun_time": datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-6))).strftime("%m-%d %H:%M:%S")
        })

    def get_all_data(self):
        """Combine solar position with sunrise/sunset times."""
        return {**self.sun_times, **self.solar_position}
