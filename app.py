from flask import Flask, render_template
from flask_socketio import SocketIO

from modules.weather_module import Weatherman
from modules.solar_module import SolarCalculator
from modules.server_module import IndigoServer
from modules import arduino_module
from utilities.config import RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD
from modules import mount_module

# === App Init ===
app = Flask(__name__)
socketio = SocketIO(app)

# === Module Instances ===
weatherman = Weatherman()
solar_calculator = SolarCalculator()
indigo = IndigoServer(RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD)
mount_module.set_socketio(socketio)
mount = mount_module.MountController(RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD)

# === Routes ===
@app.route('/')
def index():
    return render_template('index.html')

# === WebSocket Handlers ===

# Weather Handler
@socketio.on('get_weather')
def send_weather_now():
    socketio.emit("update_weather", weatherman.get_data())

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
@socketio.on('mount_command')
def handle_mount_command(data):
    cli_args = data.get("args", "")
    if cli_args:
        mount.run_indigo_prop_command(cli_args, lambda msg: socketio.emit("server_log", msg))

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

@socketio.on("get_mount_coordinates")
def handle_get_mount_coordinates():
    coords = mount.get_coordinates()
    socketio.emit("mount_coordinates", coords)

# Arduino Control
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

# === Start App ===
if __name__ == '__main__':
    weatherman.start_monitor(socketio, interval=600)
    solar_calculator.start_monitor(socketio, interval=5)
    mount._start_coord_monitor()  # Start continuous coordinate updates
    socketio.run(app, host='0.0.0.0', port=5001)