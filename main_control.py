# Main control script to run 
# the startup, tracking, weather monitoring, and shutdown scripts.
# GUI and command-line modes are supported.

import argparse
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext

def run_script(script_name, output_box=None):
    """Run a script as a subprocess and optionally display output in a GUI box."""
    process = subprocess.Popen(['python', script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    
    if output_box:
        output_box.insert(tk.END, f"Output of {script_name}:\n{stdout}\n")
        if stderr:
            output_box.insert(tk.END, f"Errors:\n{stderr}\n")
        output_box.see(tk.END)
    else:
        print(f"Output of {script_name}:\n{stdout}")
        if stderr:
            print(f"Errors:\n{stderr}")

def main():
    """ Automatically run the startup, tracking, and weather monitoring scripts."""

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

def run_gui():
    """ Create a GUI with buttons to run the scripts and display output."""

    def create_button(script_name):
        frame = tk.Frame(root)
        frame.pack(pady=5)
        
        button = tk.Button(frame, text=f"Run {script_name}", command=lambda: threading.Thread(target=run_script, args=(script_name, output_box)).start())
        button.pack(side=tk.LEFT)
        
        output_box = scrolledtext.ScrolledText(frame, width=60, height=5)
        output_box.pack(side=tk.LEFT, padx=10)
        
        return button

    root = tk.Tk()
    root.title("Automated Solar Telescope Control Panel")

    start_server_button = create_button('start_server.py')
    startup_button = create_button('startup_mount.py')
    tracking_button = create_button('track_sun.py')
    weather_button = create_button('weather_monitor.py')
    run_fc_button = create_button('run_fc.py')
    shutdown_button = create_button('shutdown_mount.py')
    nstep_button = create_button('nstep_control.py')
    kill_server_button = create_button('kill_server.py')

    root.mainloop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scripts in command-line or GUI mode.")
    parser.add_argument('--mode', choices=['auto', 'gui'], default='auto', help="Mode to run the scripts: 'auto' for command-line, 'gui' for GUI.")
    args = parser.parse_args()

    if args.mode == 'auto':
        main()
    elif args.mode == 'gui':
        run_gui()
