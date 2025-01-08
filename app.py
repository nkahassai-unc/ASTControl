from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import threading
import time
import json
from peripherals.weather_monitor import WeatherMonitor
from mount.solar_calc import SolarCalculator  # Adjust the import based on your project structure

app = Flask(__name__)
socketio = SocketIO(app)

manual_refresh_requested = threading.Event()
data_lock = threading.Lock()


#WEATHER MONITORING

# Shared weather data and manual refresh flag
weather_data = {
    "temperature": "--",
    "sky_conditions": "Unknown",
    "wind_speed": "--",
    "last_checked": None
}

def weather_thread():
    """Weather monitoring thread for periodic and manual updates."""
    weather_monitor = WeatherMonitor()
    print("Weather thread started")
    while True:
        try:
            # Fetch weather data
            latest_data = weather_monitor.check_weather()
            with data_lock:
                weather_data.update(latest_data)
            print(f"Weather updated: {weather_data}")

            # Wait for 20 minutes or a manual refresh
            if not manual_refresh_requested.wait(timeout=20 * 60):  # Timeout of 20 minutes
                continue
            print("Manual refresh triggered")
            manual_refresh_requested.clear()  # Reset the event

        except Exception as e:
            print(f"Error in weather monitor thread: {e}")


@app.route('/refresh_weather', methods=['GET'])
def refresh_weather():
    """Manual weather refresh endpoint."""
    manual_refresh_requested.set()  # Trigger immediate refresh
    with data_lock:
        return jsonify(weather_data)

#SOLAR CALCULATIONS

# Shared solar data
solar_data = {"altitude": "--", "azimuth": "--", "sunrise": "--", "sunset": "--", "solar_noon": "--", "last_updated": None}
solar_calculator = SolarCalculator()

def update_solar_info():
    """Update solar position every 20 seconds and sunrise/sunset every 12 hours."""
    while True:
        with data_lock:
            solar_calculator.update_solar_position()
            solar_data.update(solar_calculator.get_all_data())
        socketio.emit("solar_update", solar_data)
        threading.Event().wait(20)  # Update solar position every 20 seconds

def refresh_sun_times():
    """Update sunrise and sunset data every 12 hours."""
    while True:
        solar_calculator.update_sun_times()
        threading.Event().wait(12 * 60 * 60)  # Refresh every 12 hours

@app.route('/refresh_solar', methods=['GET'])
def refresh_solar():
    """Return current solar data."""
    with data_lock:
        return jsonify(solar_data)
    
# Serve the homepage
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__': 
    # Start weather monitor thread
    threading.Thread(target=weather_thread, daemon=True).start()
    # Start solar monitor thread
    threading.Thread(target=update_solar_info, daemon=True).start()
    threading.Thread(target=refresh_sun_times, daemon=True).start()
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)