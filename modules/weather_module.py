# Weather Module
# Description: Module to monitor weather conditions using OpenWeatherMap API.

import requests
import threading
import time
from datetime import datetime
from utilities.config import WEATHER_API_KEY, DEFAULT_WEATHER_DATA

class WeatherMonitor:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        self.api_url = 'http://api.openweathermap.org/data/2.5/weather'
        self.api_key = WEATHER_API_KEY
        self.latitude = latitude
        self.longitude = longitude
        self._data = DEFAULT_WEATHER_DATA.copy()
        self.weather_data = {
            'temperature': "--",
            'wind_speed': "--",
            'rain_chance': "--",
            'sky_conditions': "unknown",
            'last_checked': "--"
        }

    @property
    def latest_data(self):
        return self._data

    def check_weather(self):
        try:
            res = requests.get(self.api_url, params={
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key,
                'units': 'metric'
            }, timeout=5)
            res.raise_for_status()
            data = res.json()

            weather = [w['main'].lower() for w in data.get('weather', [])]
            self.weather_data = {
                'temperature': round(data['main'].get('temp', 0), 2),
                'wind_speed': data['wind'].get('speed', "--"),
                'rain_chance': data.get('rain', {}).get('1h', 0),
                'sky_conditions': 'clear' if 'clear' in weather else 'not clear',
                'last_checked': datetime.now().strftime('%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"[WeatherMonitor] Error fetching weather: {e}")

    def get_data(self):
        return self.weather_data

    def start_monitor(self, socketio, interval=1200):
        def loop():
            while True:
                self.check_weather()
                socketio.emit("weather_update", self.weather_data)
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()