# Demo of controlling etalons with a GUI
# WIP - not tested yet, to be tested with the actual hardware

import serial
import tkinter as tk
from tkinter import ttk

# Connect to Arduino
arduino = serial.Serial('COM3', 9600)  # Replace 'COM3' with the appropriate port

# GUI setup
root = tk.Tk()
root.title("Servo Control")
root.geometry("300x200")

# Servo 1 slider
servo1_label = ttk.Label(root, text="Servo 1")
servo1_label.pack()
servo1_slider = ttk.Scale(root, from_=0, to=180, orient=tk.HORIZONTAL)
servo1_slider.pack()

# Servo 2 slider
servo2_label = ttk.Label(root, text="Servo 2")
servo2_label.pack()
servo2_slider = ttk.Scale(root, from_=0, to=180, orient=tk.HORIZONTAL)
servo2_slider.pack()

# Function to send servo positions to Arduino
def update_servos():
    servo1_pos = servo1_slider.get()
    servo2_pos = servo2_slider.get()
    arduino.write(f"{servo1_pos},{servo2_pos}\n".encode())

# Button to update servo positions
update_button = ttk.Button(root, text="Update", command=update_servos)
update_button.pack()

# Main loop
root.mainloop()