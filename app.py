# Flask App for Automated Solar Telescope Control

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

import requests
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO

from utilities.config import RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD, FILE_STATUS
from utilities.network_utils import run_pi_ssh_command

from modules.weather_module import WeatherForecast
from modules.solar_module import SolarPosition

from modules.file_module import start_file_monitoring, get_file_list

from modules.server_module import IndigoRemoteServer
from modules.server_module import indigo_client, start_indigo_client

from modules.nstep_module import NStepFocuser, set_socketio as set_nstep_socketio
from modules.mount_module import MountControl, set_socketio as set_mount_socketio
from modules import arduino_module


# === App Init ===
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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


# Attach shared socket
set_nstep_socketio(socketio)
set_mount_socketio(socketio)
arduino_module.set_socketio(socketio)

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html', pi_ip=RASPBERRY_PI_IP)

# === WebSocket Handlers ===

# Weather Handler
@socketio.on('get_weather')
def send_weather_now():
    socketio.emit("update_weather", weather_forecast.get_data())

# Solar Handler
@socketio.on('get_solar')
def send_solar_now():
    socketio.emit("update_solar", solar_calculator.get_data())

@socketio.on("get_mount_solar_state")
def handle_get_mount_solar_state():
    solar_coords = solar_calculator.get_solar_equatorial()
    mount_coords = mount.get_coordinates()  # You’ll define this separately
    socketio.emit("mount_solar_state", {
        **solar_coords,
        **mount_coords
    })


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
    socketio.emit("indigo_status", {
        "running": is_up,
        "ip": RASPBERRY_PI_IP if is_up else None
    })

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
    nstep.move(direction)
    nstep.get_position()  # Optionally request update right after move

@socketio.on("get_nstep_position")
def handle_get_nstep_position():
    nstep.get_position()


# File Handlers
@app.route("/get_file_list")
def get_file_list_route():
    try:
        return jsonify(get_file_list())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Arduino Handlers
@socketio.on('set_dome')
def handle_set_dome(data):
    state_cmd = data.get("state")  # should be "open" or "close"
    if state_cmd and arduino_module.set_dome(state_cmd):
        socketio.emit("dome_state", arduino_module.get_dome())
    else:
        socketio.emit("server_log", f"⚠️ Failed to set dome state: {state_cmd}")

@socketio.on('set_etalon')
def handle_set_etalon(data):
    index = int(data.get("index", 0))
    value = int(data.get("value", 90))
    if arduino_module.set_etalon(index, value):
        socketio.emit("etalon_position", {
            "index": index,
            "value": arduino_module.get_etalon(index)
        })
    else:
        socketio.emit("server_log", f"⚠️ Failed to set etalon {index} to {value}")

@socketio.on('get_arduino_state')
def handle_get_arduino_state():
    state = arduino_module.get_state()
    socketio.emit("arduino_state", state)

# Science Camera Handlers
preview_running = False  # Global state

@socketio.on("start_fc_preview")
def handle_start_fc_preview():
    try:
        run_pi_ssh_command("/home/pi/fc_stream/start_fc_http_server.sh")
        run_pi_ssh_command("/home/pi/fc_stream/fc_preview_stream.sh &")
        socketio.emit("server_log", "✅ FireCapture preview and HTTP server started.")
    except Exception as e:
        socketio.emit("server_log", f"❌ Preview failed: {e}")

@socketio.on("stop_fc_preview")
def handle_stop_fc_preview():
    try:
        run_pi_ssh_command("pkill -f fc_preview_stream.sh")
        run_pi_ssh_command("pkill -f 'http.server 8082'")
        socketio.emit("server_log", "🛑 FireCapture preview stopped.")
    except Exception as e:
        socketio.emit("server_log", f"❌ Failed to stop preview: {e}")

@socketio.on("trigger_fc_capture")
def handle_fc_capture():
    try:
        run_pi_ssh_command("cd /home/pi/fc_capture && DISPLAY=:0 ./trigger_fc_script.sh")
        socketio.emit("server_log", "📸 Capture triggered.")
    except Exception as e:
        socketio.emit("server_log", f"❌ Capture failed: {e}")

@socketio.on("get_fc_status")
def handle_get_fc_status():
    socketio.emit("fc_preview_status", preview_running)

# === Start App ===
if __name__ == '__main__':
    weather_forecast.start_monitor(socketio, interval=600)
    solar_calculator.start_monitor(socketio, interval=5)
    arduino_module.start_monitor(interval=1)
    socketio.start_background_task(start_file_monitoring, 5)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("Starting Flask app on http://localhost:5001...")
    socketio.run(app, host='0.0.0.0', port=5001)