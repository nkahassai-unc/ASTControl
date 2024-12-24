# Ensure this is the very first import before any other
import eventlet
eventlet.monkey_patch()

import json
import time
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import threading
import peripherals.weather_monitor as weather_monitor
from server.start_server import StartServer  # Adjust the import if necessary

app = Flask(__name__)
socketio = SocketIO(app)

# Centralized status store for managing script states and outputs
status_store = {
    "server": "stopped",
    "weather": {
        "temperature": "--",
        "rain_chance": "--",
        "sky_conditions": "--",
        "last_checked": "Not yet started"
    }
}

# Dictionary to store threads for scripts
script_threads = {}

# Function to log output and emit updates via SocketIO
def log_output(script_name, log_message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        data = json.loads(log_message)
        if 'temperature' in data:
            # Update weather status
            status_store["weather"] = {
                "temperature": data['temperature'],
                "rain_chance": data['rain_chance'],
                "sky_conditions": data['sky_conditions'],
                "last_checked": data['last_checked']
            }
            socketio.emit('weather_update', status_store["weather"])
    except json.JSONDecodeError:
        message = f"[{timestamp}] {log_message}"
        socketio.emit(f'{script_name}_update', {'message': message})

# Function to start a script and manage its thread
def start_script(script_name):
    if script_name == "weather_monitor":
        if "weather_monitor" not in script_threads or not script_threads["weather_monitor"].is_alive():
            weather_thread = threading.Thread(target=weather_monitor.main, args=(lambda msg: log_output("weather", msg),))
            weather_thread.daemon = True
            weather_thread.start()
            script_threads["weather_monitor"] = weather_thread
            log_output("weather_monitor", "Weather monitor started.")

    elif script_name == "start_server":
        if "start_server" not in script_threads:
            server_starter = StartServer(lambda msg: log_output("start_server", msg))
            server_thread = threading.Thread(target=server_starter.run)
            server_thread.daemon = True
            server_thread.start()
            script_threads["start_server"] = server_thread
            log_output("start_server", "INDIGO server started.")

# Flask route to start a script
@app.route('/start/<script_name>', methods=['POST'])
def start_script_route(script_name):
    if script_name in ["weather_monitor", "start_server"]:
        start_script(script_name)
        return jsonify({"status": f"{script_name} started"})
    else:
        return jsonify({"status": f"{script_name} not recognized"})

# Flask route to get the current status of all scripts
@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(status_store)

# Serve the homepage
@app.route('/')
def home():
    return render_template('index.html', weather=status_store["weather"])

# Main entry point
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
