from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import threading
import time

from utilities.weather_monitor import WeatherMonitor
from utilities.solar_calc import SolarCalculator
from server.server_con import IndigoServerController

app = Flask(__name__)
socketio = SocketIO(app)

data_lock = threading.Lock()

# Shared weather data
weather_data = {
    "temperature": "--",
    "sky_conditions": "Unknown",
    "wind_speed": "--",
    "last_checked": None
}

# Shared solar data
solar_data = {
    "solar_alt": "--", "solar_az": "--", 
    "sunrise": "--", "sunset": "--", 
    "solar_noon": "--", "sun_time": None
}

# Instantiate monitors
weather_monitor = WeatherMonitor()
solar_calculator = SolarCalculator()

def weather_thread():
    """Thread to update weather data and emit real-time updates."""
    print("Weather thread started")
    while True:
        try:
            # Update weather data
            latest_data = weather_monitor.check_weather()
            with data_lock:
                weather_data.update(latest_data)
            socketio.emit("weather_update", weather_data)  # Emit updated data to clients
            print(f"Weather updated: {weather_data}")
            time.sleep(1200)  # Update every 20 minutes
        except Exception as e:
            print(f"Error in weather monitor thread: {e}")

def solar_thread():
    """Thread to update solar data and emit real-time updates."""
    print("Solar thread started")
    while True:
        try:
            with data_lock:
                solar_calculator.update_solar_position()
                solar_data.update(solar_calculator.get_all_data())
            socketio.emit("solar_update", solar_data)  # Emit updated data to clients
            print(f"Solar data updated: {solar_data}")
            time.sleep(20)  # Update every 20 seconds
        except Exception as e:
            print(f"Error in solar monitor thread: {e}")

# Raspberry Pi Details
RASPBERRY_PI_IP = "192.168.1.183"
USERNAME = "pi"
PASSWORD = "raspberry"

# INDIGO Server Controller
server_controller = IndigoServerController(
    ip=RASPBERRY_PI_IP,
    username=USERNAME,
    password=PASSWORD,
    log_callback=lambda message: socketio.emit("server_log", message),
)

# Server Endpoints
@app.route("/start_server", methods=["POST"])
def start_server():
    """Start the INDIGO server on the Raspberry Pi."""
    result = server_controller.start_indigo_server()
    return jsonify({"status": "success", "message": result})

@app.route("/kill_server", methods=["POST"])
def kill_server():
    """Kill the INDIGO server on the Raspberry Pi."""
    result = server_controller.kill_indigo_server()
    return jsonify({"status": "success", "message": result})

# Weather Endpoint
@app.route('/refresh_weather', methods=['GET'])
def refresh_weather():
    """Return current weather data."""
    with data_lock:
        return jsonify(weather_data)

# Solar Endpoint
@app.route('/refresh_solar', methods=['GET'])
def refresh_solar():
    """Return current solar data."""
    with data_lock:
        return jsonify(solar_data)

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # Start threads for real-time updates
    threading.Thread(target=weather_thread, daemon=True).start()
    threading.Thread(target=solar_thread, daemon=True).start()

    # Run Flask app with Socket.IO
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)