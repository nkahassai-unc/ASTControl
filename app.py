from flask import Flask, jsonify, render_template
import threading
import time
from collections import deque
import subprocess
import weather_monitor  # Import your weather_monitor script

app = Flask(__name__)

# Dictionary to keep track of output for each script
script_outputs = {
    "weather_monitor.py": deque(maxlen=20),
    "nstep_control.py": deque(maxlen=20),
    "start_server.py": deque(maxlen=20),
    "kill_server.py": deque(maxlen=20),
    "run_fc.py": deque(maxlen=20),
    "startup_mount.py": deque(maxlen=20),
}

# To prevent multiple weather monitor threads
weather_monitor_thread = None
# Dictionary to store threads for other scripts
script_threads = {}

# Function to log output to a script's deque
def log_output(script_name, log_message):
    """Logs output with a timestamp."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    script_outputs[script_name].append(f"[{timestamp}] {log_message}")

# Function to execute a Python script using subprocess and capture real-time output
def run_script_with_subprocess(script_name, script_command):
    log_output(script_name, f"Starting {script_name}...")
    try:
        # Start the script and capture its output
        process = subprocess.Popen(
            ['python3', script_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Capture real-time output
        for line in process.stdout:
            log_output(script_name, line.strip())

        # Wait for the process to complete
        process.wait()

        # Capture any errors
        for line in process.stderr:
            log_output(script_name, line.strip())

        log_output(script_name, f"{script_name} completed.")
    except Exception as e:
        log_output(script_name, f"Error running {script_name}: {str(e)}")

# Function to start a script in a new thread
def start_script_in_thread(script_name, script_command):
    # If the script is already running, don't start another thread
    if script_name in script_threads and script_threads[script_name].is_alive():
        log_output(script_name, f"{script_name} is already running.")
        return
    
    # Start the script in a new thread
    script_thread = threading.Thread(target=run_script_with_subprocess, args=(script_name, script_command))
    script_thread.daemon = True  # Daemonize thread
    script_thread.start()
    script_threads[script_name] = script_thread

# Function to run weather_monitor.py every 5 minutes
def run_periodic_weather_monitor():
    while True:
        log_output("weather_monitor.py", "Starting weather monitor check...")
        weather_monitor.main(lambda msg: log_output("weather_monitor.py", msg))
        log_output("weather_monitor.py", "Weather monitor check completed.")
        time.sleep(300)  # Sleep for 5 minutes

# Function to start the appropriate script (either in a thread or periodically for weather)
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
    else:
        # Start other scripts in a new thread
        script_mapping = {
            "nstep_control.py": "nstep_control.py",
            "run_fc.py": "run_fc.py",
            "startup_mount.py": "startup_mount.py",
            "start_server.py": "start_server.py",
            "kill_server.py": "kill_server.py"
        }
        if script_name in script_mapping:
            start_script_in_thread(script_name, script_mapping[script_name])
        else:
            log_output(script_name, f"{script_name} not recognized.")

# Flask route to start a script
@app.route('/start/<script_name>')
def start_script(script_name):
    if script_name in script_outputs:
        run_script(script_name)
        return jsonify({"status": f"{script_name} started"})
    else:
        return jsonify({"status": f"{script_name} not recognized"})

# Flask route to fetch the last 20 lines of output for any script
@app.route('/output/<script_name>')
def get_output(script_name):
    if script_name in script_outputs:
        output = list(script_outputs[script_name])  # Convert deque to list
        return jsonify({"output": output})
    else:
        return jsonify({"output": f"{script_name} not running or not recognized"})

# Flask route to serve the homepage (index.html)
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
