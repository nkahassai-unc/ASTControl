import requests
from datetime import datetime

class WeatherMonitor:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        """Initialize with API key and location."""
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
        self.api_key = '10b2f1d4a200b534bb2d4bf69bddcace'
        self.latitude = latitude
        self.longitude = longitude

    def check_weather(self):
        """Fetch current weather conditions."""
        try:
            response = requests.get(
                self.weather_api_url,
                params={
                    'lat': self.latitude,
                    'lon': self.longitude,
                    'appid': self.api_key,
                    'units': 'metric'
                }
            )
            response.raise_for_status()
            data = response.json()

            # Extract relevant fields
            weather_conditions = [condition['main'].lower() for condition in data.get('weather', [])]
            temperature = data['main'].get('temp', '--')
            rain_chance = data.get('rain', {}).get('1h', 0)
            sky_conditions = 'clear' if 'clear' in weather_conditions else 'not clear'

            return {
                'temperature': round(temperature, 2),
                'rain_chance': rain_chance,
                'sky_conditions': sky_conditions,
                'last_checked': datetime.now().strftime('%m-%d %H:%M:%S')
            }
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return {"error": "Unable to fetch weather data"}
