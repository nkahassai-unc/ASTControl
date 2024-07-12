# Weather Monitor script to check weather conditions 
# Initiate shutdown if rain is likely.

import requests
import time
import subprocess

class WeatherMonitor:
    def __init__(self):
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
        
        #OpenWeatherMap API Key
        self.weather_api_key = '10b2f1d4a200b534bb2d4bf69bddcace'
        self.latitude = 35.9132  # Latitude of Chapel Hill, NC
        self.longitude = -79.0558  # Longitude of Chapel Hill, NC

    def run_command(self, command):
        """Execute a shell command."""
        try:
            result = subprocess.run(command, shell=True, check=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def check_weather(self):
        """Check current weather conditions and return if rain is likely."""
        try:
            response = requests.get(
                self.weather_api_url,
                params={
                    'lat': self.latitude,
                    'lon': self.longitude,
                    'appid': self.weather_api_key
                }
            )
            data = response.json()

            weather_conditions = [condition['main'].lower() for condition in data['weather']]
            if 'rain' in weather_conditions:
                return True
            return False
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return False

    def monitor_and_shutdown(self):
        """Monitor weather conditions and initiate shutdown if needed."""
        
        # Check weather every 15 minutes
        while True:
            if self.check_weather():
                print("Unfavorable weather detected. Initiating shutdown sequence...")
                self.run_command('python3 shutdown_mount.py')
                break
            time.sleep(900)  # 15 minutes

def main():
    weather_monitor = WeatherMonitor()
    weather_monitor.monitor_and_shutdown()

if __name__ == "__main__":
    main()