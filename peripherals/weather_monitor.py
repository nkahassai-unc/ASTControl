import requests
import time
import json

class WeatherMonitor:
    def __init__(self, output_callback, update_interval=900):
        """Initialize with the output callback function."""
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
        self.weather_api_key = '10b2f1d4a200b534bb2d4bf69bddcace'  # Replace with your actual API key
        self.latitude = 35.9132
        self.longitude = -79.0558
        self.output_callback = output_callback
        self.update_interval = update_interval

    def log(self, message):
        """Log output through the callback to app.py"""
        self.output_callback(message)

    def check_weather(self):
        """Check current weather conditions and log the output."""
        try:
            response = requests.get(
                self.weather_api_url,
                params={
                    'lat': self.latitude,
                    'lon': self.longitude,
                    'appid': self.weather_api_key,
                    'units': 'metric'
                }
            )
            response.raise_for_status()
            data = response.json()

            weather_conditions = [condition['main'].lower() for condition in data['weather']]
            temperature = data['main']['temp']
            rain_chance = data.get('rain', {}).get('1h', 0)
            sky_conditions = 'clear' if 'clear' in weather_conditions else 'not clear'

            weather_data = {
                'temperature': temperature,
                'rain_chance': rain_chance,
                'sky_conditions': sky_conditions,
                'last_checked': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            self.log(json.dumps(weather_data))

        except requests.RequestException as e:
            self.log(f"Error fetching weather data: {str(e)}")

    def run(self):
        """Run the weather monitor continuously."""
        self.log("Weather monitor started.")
        while True:
            self.check_weather()
            time.sleep(self.update_interval)

def main(output_callback):
    """Main function for running the weather monitor."""
    weather_monitor = WeatherMonitor(output_callback)
    weather_monitor.run()

# Standalone testing
if __name__ == "__main__":
    def output_callback(log_message):
        print(log_message)
    main(output_callback)
