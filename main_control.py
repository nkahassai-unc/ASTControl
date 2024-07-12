# Main control script to run the startup, tracking, 
# weather monitoring, and shutdown scripts.

import threading
import subprocess

def run_script(script_name):
    """Run a script as a subprocess."""
    subprocess.run(['python3', script_name])

def main():
    # Run the startup script to initialize the mount
    print("Initializing mount with startup script...")
    run_script('startup_mount.py')
    print("Mount initialization complete.")

    # Start the tracking script
    print("Starting tracking.")
    tracking_thread = threading.Thread(target=run_script, args=('track_sun.py',))
    tracking_thread.start()

    # Start the weather monitoring script
    print("Starting Weather Monitor.")
    weather_thread = threading.Thread(target=run_script, args=('weather_monitor.py',))
    weather_thread.start()

    tracking_thread.join()
    weather_thread.join()

if __name__ == "__main__":
    main()