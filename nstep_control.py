# Demo of controlling nSTEP with a GUI
# WIP - not tested yet, to be tested with the actual hardware

import tkinter as tk
from tkinter import messagebox
import subprocess
import time as pytime

class FocuserControl:
    def __init__(self, master):
        self.master = master
        self.master.title("nSTEP Focuser Control")

        # Connect to the focuser
        self.connect_focuser()

        # Create GUI elements
        self.create_widgets()

        # Update position and temperature periodically
        self.update_position_and_temperature()

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def connect_focuser(self):
        # Connect the focuser
        print("Connecting to the focuser...")
        self.run_command(f"indigo_prop_tool set \"nSTEP.CONNECTION.CONNECTED=ON\"")
        
        # Wait until the focuser is connected
        while True:
            status = self.run_command(f"indigo_prop_tool get \"nSTEP.CONNECTION.CONNECTED\"").strip()
            if status == "ON":
                print("Focuser connected.")
                break
            else:
                print("Waiting for focuser to connect...")
                pytime.sleep(3)  # Wait 3 seconds before checking again

    def create_widgets(self):
        # Speed control
        tk.Label(self.master, text="Speed:").grid(row=0, column=0)
        self.speed_var = tk.DoubleVar(value=241.0)
        self.speed_scale = tk.Scale(self.master, from_=0, to=500, orient=tk.HORIZONTAL, variable=self.speed_var)
        self.speed_scale.grid(row=0, column=1)
        tk.Button(self.master, text="Set Speed", command=self.set_speed).grid(row=0, column=2)

        # Direction control
        tk.Label(self.master, text="Direction:").grid(row=1, column=0)
        self.direction_var = tk.StringVar(value="MOVE_INWARD")
        tk.Radiobutton(self.master, text="Inward", variable=self.direction_var, value="MOVE_INWARD").grid(row=1, column=1)
        tk.Radiobutton(self.master, text="Outward", variable=self.direction_var, value="MOVE_OUTWARD").grid(row=1, column=2)
        tk.Button(self.master, text="Move", command=self.set_direction).grid(row=1, column=3)

        # Abort motion
        tk.Button(self.master, text="Abort Motion", command=self.abort_motion).grid(row=2, column=0, columnspan=4)

        # Position and temperature readout
        tk.Label(self.master, text="Position:").grid(row=3, column=0)
        self.position_label = tk.Label(self.master, text="0")
        self.position_label.grid(row=3, column=1)

        tk.Label(self.master, text="Temperature:").grid(row=4, column=0)
        self.temperature_label = tk.Label(self.master, text="0")
        self.temperature_label.grid(row=4, column=1)

    def set_speed(self):
        speed = self.speed_var.get()
        # Set the focuser speed using indigo_prop_tool
        self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_SPEED.SPEED={speed}\"")
        messagebox.showinfo("Info", f"Speed set to {speed}")

    def set_direction(self):
        direction = self.direction_var.get()
        if direction == "MOVE_INWARD":
            self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_DIRECTION.MOVE_INWARD=ON\"")
            self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_DIRECTION.MOVE_OUTWARD=OFF\"")
        else:
            self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_DIRECTION.MOVE_INWARD=OFF\"")
            self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_DIRECTION.MOVE_OUTWARD=ON\"")
        messagebox.showinfo("Info", f"Direction set to {direction}")

    def abort_motion(self):
        self.run_command(f"indigo_prop_tool set \"nSTEP.FOCUSER_ABORT_MOTION.ABORT_MOTION=ON\"")
        messagebox.showinfo("Info", "Motion aborted")

    def update_position_and_temperature(self):
        # Get the current position and temperature from indigo_prop_tool
        position = self.run_command(f"indigo_prop_tool get \"nSTEP.FOCUSER_POSITION.POSITION\"").strip()
        temperature = self.run_command(f"indigo_prop_tool get \"nSTEP.FOCUSER_TEMPERATURE.TEMPERATURE\"").strip()

        # Update the labels
        self.position_label.config(text=position)
        self.temperature_label.config(text=temperature)

        # Schedule the update function to run again after 1 second
        self.master.after(1000, self.update_position_and_temperature)

if __name__ == "__main__":
    root = tk.Tk()
    focuser_control = FocuserControl(root)
    root.mainloop()
