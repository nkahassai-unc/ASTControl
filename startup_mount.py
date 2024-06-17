# Startup script to initialize the mount with location and home coordinates.

import subprocess
import time

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount Simulator'
        self.latitude = 35.913200 #N 
        self.longitude = 280.944153 #E 
        self.altitude = 80

        self.initialize_mount()

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def initialize_mount(self):
        """Initialize the mount with location and home coordinates."""
        print("Setting the location...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.GEOGRAPHIC_COORDINATES.LATITUDE={self.latitude};LONGITUDE={self.longitude};ELEVATION={self.altitude}\"")
        time.sleep(5)  # Wait for the mount to sync with the location

        print("Syncing the telescope with home coordinates...")
        home_ra = 0.0
        home_dec = 90.0
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={home_ra};DEC={home_dec}\"")
        time.sleep(5)  # Wait for the mount to sync with the home coordinates

        print("Unhoming the mount...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_HOME.HOME=OFF\"")
        time.sleep(5)  # Wait for the mount to unhome

        print("Setting the solar tracking rate...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACK_RATE.SOLAR=ON\"")
        time.sleep(5)  # Wait for the mount to set the tracking rate


if __name__ == "__main__":
    mount_control = MountControl()