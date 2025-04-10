from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

from modules.weather_module import WeatherMonitor
from modules.solar_module import SolarCalculator
from modules.server_module import IndigoServer
from modules import arduino_module
from utilities.config import RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD

# === App Init ===
app = Flask(__name__)
socketio = SocketIO(app)

# === Module Instances ===
weather_monitor = WeatherMonitor()
solar_calculator = SolarCalculator()
indigo = IndigoServer(RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD)

# === ROUTES ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_server', methods=['POST'])
def start_server():
    indigo.start(lambda msg: socketio.emit("server_log", msg))
    return jsonify({"status": "started", "ip_status": RASPBERRY_PI_IP})

@app.route('/kill_server', methods=['POST'])
def kill_server():
    result = indigo.stop()
    return jsonify({
        "status": "stopped",
        "message": result.get("stdout", ""),
        "ip_status": RASPBERRY_PI_IP
    })

@app.route('/refresh_weather')
def refresh_weather():
    return jsonify(weather_monitor.latest_data)

@app.route('/refresh_solar')
def refresh_solar():
    return jsonify(solar_calculator.get_data())

@app.route('/refresh_arduino')
def refresh_arduino():
    return jsonify(arduino_module.get_state())

@app.route('/set_dome', methods=['POST'])
def set_dome():
    data = request.get_json()
    state_cmd = data.get("state")
    success = arduino_module.set_dome(state_cmd)
    return jsonify({"success": success, "state": arduino_module.get_dome()})

@app.route('/set_etalon', methods=['POST'])
def set_etalon():
    data = request.get_json()
    index = int(data.get("index", 0))
    value = int(data.get("value", 90))
    success = arduino_module.set_etalon(index, value)
    return jsonify({"success": success, "value": arduino_module.get_etalon(index)})

# === Start Flask App ===
if __name__ == '__main__':
    weather_monitor.start_monitor(socketio)
    solar_calculator.start_monitor(socketio)
    #arduino_module.start_monitor()
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
