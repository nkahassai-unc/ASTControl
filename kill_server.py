# Script to kill Indigo server and Indigo Web Server

import subprocess

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output.decode(), error.decode()

commands = ["sudo pkill -f indigo_server", "sudo pkill -f indigo_wo"]

for command in commands:
    output, error = run_command(command)
    print(f"Running command: {command}")
    print("Output:", output)
    print("Error:", error)