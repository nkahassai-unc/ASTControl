# Weather Monitor script to check weather conditions 
# and initiate shutdown if rain is likely.

import requests
import time
import subprocess

class WeatherMonitor:
    def __init__(self):
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
        self.weather_api_key = 'YOUR_API_KEY'  # Replace with your actual API key
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

    def print_initial_weather(self):
        """Print the initial weather conditions."""
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
            
            weather_conditions = ', '.join([condition['main'] for condition in data['weather']])
            rain = data.get('rain', {}).get('1h', 0)
            clouds = data['clouds']['all']
            
            print(f"Initial weather conditions: {weather_conditions}")
            print(f"Rain (last hour): {rain} mm")
            print(f"Cloudiness: {clouds}%")

        except Exception as e:
            print(f"Error fetching initial weather data: {e}")    
    
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
        while True:
            if self.check_weather():
                print("Unfavorable weather detected. Initiating shutdown sequence...")
                self.run_command('python3 shutdown_mount.py')
                break
            time.sleep(900)  # Check weather every 15 minutes

def main():
    weather_monitor = WeatherMonitor()
    weather_monitor.print_initial_weather()  # Print initial weather conditions
    weather_monitor.monitor_and_shutdown()

if __name__ == "__main__":
    main()