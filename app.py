# Flask App for Automated Solar Telescope Control

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

from flask import Flask, render_template
from flask_socketio import SocketIO

from utilities.config import RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD
from modules.weather_module import WeatherForecast
from modules.solar_module import SolarPosition
from modules.file_module import FileHandler

from modules.server_module import IndigoRemoteServer
from modules.server_module import indigo_client, start_indigo_client

from modules.nstep_module import NStepFocuser, set_socketio as set_nstep_socketio
from modules.mount_module import MountControl, set_socketio as set_mount_socketio
# from modules.arduino_module import ArduinoControl


# === App Init ===
app = Flask(__name__)
socketio = SocketIO(app)

# === Module Instances ===
weather_forecast = WeatherForecast()
solar_calculator = SolarPosition()

indigo = IndigoRemoteServer(RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD)

mount = MountControl(indigo_client=indigo_client)
nstep = NStepFocuser(indigo_client=indigo_client)

try:
    start_indigo_client()
except Exception as e:
    print(f"[APP] Warning: INDIGO client failed to start — {e}")

# arduino_module = ArduinoControl()

# Attach shared socket
set_nstep_socketio(socketio)
set_mount_socketio(socketio)

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

# === WebSocket Handlers ===

# Weather Handler
@socketio.on('get_weather')
def send_weather_now():
    socketio.emit("update_weather", weather_forecast.get_data())

# Solar Handler
@socketio.on('get_solar')
def send_solar_now():
    socketio.emit("update_solar", solar_calculator.get_data())


# INDIGO Server Handlers
@socketio.on('start_indigo')
def handle_start_indigo():
    indigo.start(lambda msg: socketio.emit("server_log", msg))

@socketio.on('stop_indigo')
def handle_stop_indigo():
    result = indigo.stop()
    socketio.emit("server_log", result.get("stdout", ""))

@socketio.on('check_indigo_status')
def handle_check_indigo_status():
    is_up = indigo.check_status()
    socketio.emit("indigo_status", {"running": is_up})

# Mount Handlers
@socketio.on("get_mount_coordinates")
def handle_get_mount_coordinates():
    coords = mount.get_coordinates()
    socketio.emit("mount_coordinates", coords)

@socketio.on("slew_mount")
def handle_slew_mount(data):
    mount.slew(data["direction"], data.get("rate", "solar"))

@socketio.on("stop_mount")
def handle_stop_mount():
    mount.stop()

@socketio.on("track_sun")
def handle_track_sun():
    mount.track_sun()

@socketio.on("park_mount")
def handle_park_mount():
    mount.park()

@socketio.on("unpark_mount")
def handle_unpark_mount():
    mount.unpark()

# nSTEP Focuser Handlers
@socketio.on("nstep_move")
def handle_nstep_move(data):
    direction = data.get("direction")
    speed = data.get("speed", 50)  # Default to 50% if not specified
    nstep.move(direction, speed)
    nstep.get_position()  # Optionally request update right after move

@socketio.on("get_nstep_position")
def handle_get_nstep_position():
    nstep.get_position()

# File Handlers
"""
@app.route("/get_file_list")
def get_file_list_route():
    try:
        files = file_module.get_file_list()
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""


# Arduino Handlers
'''
@socketio.on('set_dome')
def handle_set_dome(data):
    state = data.get("state")
    arduino_module.set_dome(state)
    socketio.emit("dome_state", arduino_module.get_dome())

@socketio.on('set_etalon')
def handle_set_etalon(data):
    index = int(data.get("index", 0))
    value = int(data.get("value", 90))
    arduino_module.set_etalon(index, value)
    socketio.emit("etalon_position", {
        "index": index,
        "value": arduino_module.get_etalon(index)
    })
'''

# === Start App ===
if __name__ == '__main__':
    weather_forecast.start_monitor(socketio, interval=600)
    solar_calculator.start_monitor(socketio, interval=5)
    print("Starting Flask app on http://localhost:5001...")
    socketio.run(app, host='0.0.0.0', port=5001)
