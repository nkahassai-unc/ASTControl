# Weather Monitor script to check weather conditions 
# Initiate shutdown if rain is likely.

import requests
import time
import subprocess

class WeatherMonitor:
    def __init__(self):
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
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
                    'appid': self.weather_api_key,
                    'units': 'metric'  # Use 'imperial' for Fahrenheit
                }
            )
            data = response.json()
            
            # Parsing the weather conditions
            weather_conditions = [condition['main'].lower() for condition in data['weather']]
            detailed_conditions = [condition['description'] for condition in data['weather']]
            temperature = data['main']['temp']
            rain_chance = data.get('rain', {}).get('1h', 0)

            # Determine if the sky is clear or not based on detailed conditions
            if 'clear' in weather_conditions:
                sky_conditions = 'clear'
            elif 'clouds' in weather_conditions:
                cloud_cover = next(condition['description'] for condition in data['weather'] if condition['main'].lower() == 'clouds')
                if 'few clouds' in cloud_cover or 'scattered clouds' in cloud_cover:
                    sky_conditions = 'partly cloudy'
                else:
                    sky_conditions = 'cloudy'
            else:
                sky_conditions = 'not clear'

            output = (
                f"Temperature: {temperature}°C\n"
                f"Chance of rain: {rain_chance} mm in the last hour\n"
                f"Sky conditions: {sky_conditions}\n"
            )

            # Print the weather data
            print(output)

            # Check if rain is likely
            if 'rain' in weather_conditions:
                return True
            return False
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return False

    def weather_report(self):
        """Report weather conditions and initiate shutdown if needed."""
        while True:
            print("Checking weather...")
            if self.check_weather():
                print("Unfavorable weather detected. Initiating shutdown sequence...")
                #self.run_command('python3 shutdown_mount.py')
                time.sleep(900)  # Check again in 15 minutes
            else:
                print("Weather conditions are favorable. No action required.")
                print("Checking again in 15 minutes...")
            time.sleep(900)  # Check again in 15 minutes

def main():
    weather_monitor = WeatherMonitor()
    print('Starting weather monitor...')
    weather_monitor.weather_report()

if __name__ == "__main__":
    main()
