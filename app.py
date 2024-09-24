from flask import Flask, jsonify, render_template
import threading
import time
from collections import deque
import weather_monitor  # Import your weather_monitor script

app = Flask(__name__)

# Dictionary to keep track of output for each script
script_outputs = {
    "weather_monitor.py": deque(maxlen=20),  # Store the last 20 lines of output for the weather monitor
    "nstep_control.py": deque(maxlen=20),
    "start_server.py": deque(maxlen=20),
    "kill_server.py": deque(maxlen=20),
    "run_fc.py": deque(maxlen=20),  # Add FireCapture script
}

# To prevent multiple weather monitor threads
weather_monitor_thread = None

# Function to log output to a script's deque
def log_output(script_name, log_message):
    """Callback to log output to the script's deque"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    script_outputs[script_name].append(f"[{timestamp}] {log_message}")

# Function to run weather_monitor.py every 5 minutes
def run_periodic_weather_monitor():
    while True:
        log_output("weather_monitor.py", "Starting weather monitor check...")
        weather_monitor.main(lambda msg: log_output("weather_monitor.py", msg))
        log_output("weather_monitor.py", "Weather monitor check completed.")
        time.sleep(300)  # Sleep for 5 minutes

# General function to run a Python script once (like weather_monitor, nstep_control, run_fc, etc.)
def run_script(script_name):
    global weather_monitor_thread
    if script_name == "weather_monitor.py":
        # Start the weather monitor if not already running
        if not weather_monitor_thread or not weather_monitor_thread.is_alive():
            weather_monitor_thread = threading.Thread(target=run_periodic_weather_monitor)
            weather_monitor_thread.daemon = True
            weather_monitor_thread.start()
            log_output(script_name, f"{script_name} started and will run every 5 minutes.")
        else:
            log_output(script_name, f"{script_name} is already running.")
    elif script_name == "run_fc.py":
        # Example of running run_fc.py and logging output
        log_output(script_name, "Starting FireCapture...")
        # Simulating FireCapture execution, replace with actual run logic if needed
        log_output(script_name, "FireCapture completed.")
    # Add other scripts similarly...
    else:
        log_output(script_name, f"{script_name} not yet implemented.")

# Flask route to start any script
@app.route('/start/<script_name>')
def start_script(script_name):
    if script_name in script_outputs:
        script_thread = threading.Thread(target=run_script, args=(script_name,))
        script_thread.daemon = True  # Daemonize thread to avoid blocking
        script_thread.start()
        return jsonify({"status": f"{script_name} started"})
    else:
        return jsonify({"status": f"{script_name} not recognized"})

# Flask route to fetch the last 20 lines of output for any script
@app.route('/output/<script_name>')
def get_output(script_name):
    if script_name in script_outputs:
        output = list(script_outputs[script_name])  # Convert deque to a list
        return jsonify({"output": output})
    else:
        return jsonify({"output": f"{script_name} not running or not recognized"})

# Flask route to serve the homepage (index.html)
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
