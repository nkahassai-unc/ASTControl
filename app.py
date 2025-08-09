# Flask App for Automated Solar Telescope Control

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

import requests
from flask import Flask, render_template, Response, jsonify, send_from_directory
import os
from flask_socketio import SocketIO

from utilities.config import (
    RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD, FILE_STATUS,
    LOCATION_PROFILES
)
from utilities.network_utils import run_pi_ssh_command

from modules.weather_module import WeatherForecast
from modules.astro_module import AstroPosition

from modules import file_module

from modules.server_module import IndigoRemoteServer
from modules.server_module import indigo_client, start_indigo_client
from utilities.logger import emit_log, set_socketio as set_log_socketio, get_log_history

from modules.nstep_module import NStepFocuser, set_socketio as set_nstep_socketio
from modules.mount_module import MountControl, set_socketio as set_mount_socketio
from modules import arduino_module

# === App Init ===
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
set_log_socketio(socketio)

# === Module Instances ===
weather_forecast = WeatherForecast(profile="chapel_hill")
astro = AstroPosition()
indigo = IndigoRemoteServer(RASPBERRY_PI_IP, SSH_USERNAME, SSH_PASSWORD)
mount = MountControl(indigo_client=indigo_client)
nstep = NStepFocuser(indigo_client=indigo_client)

file_module.set_socketio_instance(socketio)

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'ast_fav.png', mimetype='image/png')

@socketio.on("connect")
def send_log_history():
    for msg in get_log_history():
        socketio.emit("server_log", msg)

# File Handlers
@app.route("/get_file_list")
def get_file_list_route():
    files = file_module.get_file_list()
    for f in files:
        f["status"] = FILE_STATUS.get(f["name"], "Copied")
    return jsonify(files)

# === Weather ===
@socketio.on('get_weather')
def send_weather_now():
    socketio.emit("update_weather", weather_forecast.get_data())

# === Astro (Sun + Moon) ===
@socketio.on('get_solar')
def send_astro_now():
    # unified payload mapped to your existing solar_* keys
    socketio.emit("astro_update", astro.build_frontend_payload())

@socketio.on("get_mount_solar_state")
def handle_get_mount_target_state():
    mode = getattr(mount, "target_mode", "sun").lower()
    eq = astro.get_equatorial(mode)  # {"ra_str","dec_str"}

    mount_coords = mount.get_coordinates()
    formatted = {
        # keep legacy keys that the UI already reads
        "ra_solar": eq.get("ra_str"),
        "dec_solar": eq.get("dec_str"),
        "ra_mount": mount.format_ra(mount_coords["ra"]) if mount_coords["ra"] is not None else None,
        "dec_mount": mount.format_dec(mount_coords["dec"]) if mount_coords["dec"] is not None else None,
    }

    altaz = mount.compute_altaz()
    if altaz:
        formatted["alt_mount"] = round(altaz[0], 2)
        formatted["az_mount"]  = round(altaz[1], 2)

    socketio.emit("mount_solar_state", formatted)

# Paths
@app.route("/get_solar_path")
def get_solar_path():
    return jsonify(astro.get_full_day_path(target="sun"))

@socketio.on("get_solar_path")
def handle_get_solar_path():
    socketio.emit("solar_path_data", astro.get_full_day_path(target="sun"))

@app.route("/get_moon_path")
def get_moon_path():
    return jsonify(astro.get_full_day_path(target="moon"))

@socketio.on("get_moon_path")
def handle_get_moon_path():
    socketio.emit("moon_path_data", astro.get_full_day_path(target="moon"))

# === INDIGO Server ===
@socketio.on('start_indigo')
def handle_start_indigo():
    indigo.start(lambda msg: socketio.emit("server_log", msg))

@socketio.on('stop_indigo')
def handle_stop_indigo():
    result = indigo.stop()
    emit_log(result.get("stdout", ""))

@socketio.on('check_indigo_status')
def handle_check_indigo_status():
    is_up = indigo.check_status()
    socketio.emit("indigo_status", {"running": is_up, "ip": RASPBERRY_PI_IP if is_up else None})

# === Mount ===
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
    mount.set_target("sun")
    astro.set_target_mode("sun")  # stays in sync with mount
    socketio.emit("astro_update", astro.build_frontend_payload())
    mount.emit_status("Target set to Sun")

@socketio.on("park_mount")
def handle_park_mount():
    mount.park()

@socketio.on("unpark_mount")
def handle_unpark_mount():
    mount.unpark()

# === Target & Location Toggles ===
@socketio.on("set_target")
def handle_set_target(data):
    mode = str((data or {}).get("mode", "sun")).lower()
    mount.set_target(mode)
    astro.set_target_mode(mode)  # <<< keep astro payload mapping in sync
    socketio.emit("astro_update", astro.build_frontend_payload())

@socketio.on("toggle_target")
def handle_toggle_target():
    mount.toggle_target()
    astro.set_target_mode(getattr(mount, "target_mode", "sun"))  # <<<
    socketio.emit("astro_update", astro.build_frontend_payload())

@socketio.on("set_location_profile")
def handle_set_location_profile(data):
    profile = (data or {}).get("profile", "chapel_hill")
    mount.set_location_profile(profile)

    weather_forecast.use_profile(profile)
    weather_forecast.refresh_now(socketio)

    prof = LOCATION_PROFILES.get(profile, {})
    if isinstance(prof, dict):
        lat, lon, elev = prof.get("lat"), prof.get("lon"), prof.get("elev")
    elif isinstance(prof, (list, tuple)) and len(prof) >= 3:
        lat, lon, elev = prof[0], prof[1], prof[2]
    else:
        lat = lon = elev = None

    if None not in (lat, lon, elev):
        astro.set_observer(lat, lon, elev)
        astro.set_location_profile_label(profile)
        astro.clear_path_cache()  # <<< ensure new paths recompute for the new site

    socketio.emit("astro_update", astro.build_frontend_payload())

@socketio.on("toggle_location_profile")
def handle_toggle_location_profile():
    newp = "kansas_city" if getattr(mount, "location_profile", "chapel_hill") == "chapel_hill" else "chapel_hill"
    handle_set_location_profile({"profile": newp})

# === nSTEP Focuser ===
@socketio.on("nstep_move")
def handle_nstep_move(data):
    direction = data.get("direction")
    nstep.move(direction)
    nstep.get_position()

@socketio.on("get_nstep_position")
def handle_get_nstep_position():
    nstep.get_position()

# === Arduino ===
@socketio.on('set_dome')
def handle_set_dome(data):
    state_cmd = data.get("state")
    if state_cmd and arduino_module.set_dome(state_cmd):
        emit_log("dome_state", arduino_module.get_dome())
    else:
        emit_log(f"⚠️ Failed to set dome state: {state_cmd}")

@socketio.on('set_etalon')
def handle_set_etalon(data):
    index = int(data.get("index", 0))
    value = int(data.get("value", 90))
    if arduino_module.set_etalon(index, value):
        socketio.emit("etalon_position", {"index": index, "value": arduino_module.get_etalon(index)})
    else:
        emit_log(f"⚠️ Failed to set etalon {index} to {value}")

@socketio.on('get_arduino_state')
def handle_get_arduino_state():
    state = arduino_module.get_state()
    socketio.emit("arduino_state", state)

# === Science Camera ===
preview_running = False

@socketio.on("start_fc_preview")
def handle_start_fc_preview():
    global preview_running
    emit_log("[FIRECAPTURE] ✅ Preview and HTTP server started.")
    try:
        run_pi_ssh_command("/home/pi/fc_stream/start_fc_http_server.sh")
        run_pi_ssh_command("/home/pi/fc_stream/fc_preview_stream.sh &")
        preview_running = True
    except Exception as e:
        emit_log(f"[FIRECAPTURE] ❌ Preview failed: {e}")

@socketio.on("stop_fc_preview")
def handle_stop_fc_preview():
    global preview_running
    emit_log("[FIRECAPTURE] 🛑 Stopping preview and HTTP server...")
    if not preview_running:
        return
    try:
        run_pi_ssh_command("pkill -f fc_preview_stream.sh")
        run_pi_ssh_command("pkill -f 'http.server 8082'")
        preview_running = False
    except Exception as e:
        emit_log(f"[FIRECAPTURE] ❌ Failed to stop preview: {e}")

@socketio.on("trigger_fc_capture")
def handle_fc_capture():
    try:
        run_pi_ssh_command("cd /home/pi/fc_capture && DISPLAY=:0 ./trigger_fc_script.sh")
        emit_log("📸 [FireCapture] Capture triggered.")
    except Exception as e:
        emit_log(f"❌ [FIRECAPTURE] Capture failed: {e}")

@socketio.on("get_fc_status")
def handle_get_fc_status():
    socketio.emit("fc_preview_status", preview_running)

# === Dome Camera ping ===
@app.route("/ping_dome_status")
def ping_dome_status():
    try:
        ip = RASPBERRY_PI_IP
        url = f"http://{ip}:8080/"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            return Response("OK", status=200)
        return Response("Unavailable", status=503)
    except Exception as e:
        return Response(f"Error: {e}", status=502)

# === Start App ===
if __name__ == '__main__':
    weather_forecast.start_monitor(socketio, interval=600)
    astro.start_monitor(socketio, interval=5)
    arduino_module.start_monitor(interval=1)

    socketio.start_background_task(file_module.start_file_monitoring, 5)
    emit_log("[APP] Background tasks started.")

    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.ERROR)

    print("Starting Flask app on http://localhost:5001...")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)