import requests
import time

class WeatherMonitor:
    def __init__(self, output_callback):
        self.weather_api_url = 'http://api.openweathermap.org/data/2.5/weather'
        # Keep your actual API key here
        self.weather_api_key = '10b2f1d4a200b534bb2d4bf69bddcace'
        self.latitude = 35.9132  # Latitude of Chapel Hill, NC
        self.longitude = -79.0558  # Longitude of Chapel Hill, NC
        self.output_callback = output_callback  # Output callback function to send logs to app.py

    def log(self, message):
        """Log output through the callback to app.py"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.output_callback(f"{message}")

    def check_weather(self):
        """Check current weather conditions and log the output."""
        try:
            # Make API request to OpenWeatherMap
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

            # Extract weather data
            weather_conditions = [condition['main'].lower() for condition in data['weather']]
            temperature = data['main']['temp']
            rain_chance = data.get('rain', {}).get('1h', 0)
            sky_conditions = 'clear' if 'clear' in weather_conditions else 'not clear'

            # Log the weather details
            temp_output = (f"Temperature: {temperature}°C\n")
            rain_output = (f"Chance of rain: {rain_chance} mm in the last hour\n")
            sky_output = (f"Sky conditions: {sky_conditions}\n")

            self.log(temp_output)
            self.log(rain_output)
            self.log(sky_output)

            # Log if rain is detected
            if 'rain' in weather_conditions:
                self.log("Unfavorable weather detected. Initiating shutdown sequence...")
                # Add shutdown logic here
            else:
                self.log("Weather conditions are favorable. No action required.")

        except Exception as e:
            self.log(f"Error fetching weather data: {str(e)}")

def main(output_callback):
    weather_monitor = WeatherMonitor(output_callback)
    print('')
    print('')
    weather_monitor.check_weather()

# If this script is run independently, use this fallback
if __name__ == "__main__":
    def output_callback(log_message):
        print(log_message)  # Print to terminal for testing
    main(output_callback)
