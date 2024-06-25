# Startup script to initialize the mount with location and home coordinates.

import subprocess
import time

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount SynScan'
        self.latitude = 35.913200 #N 
        self.longitude = 280.944153 #E 
        self.altitude = 80 # meters

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
        # Connect the mount
        print("Connecting to the mount...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.CONNECTION.CONNECTED=ON\"")
        
        # Wait until the mount is connected
        while True:
            status = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.CONNECTION.CONNECTED\"").strip()
            if status == "ON":
                print("Mount connected.")
                break
            else:
                print("Waiting for mount to connect...")
                time.sleep(5)  # Wait for 5 seconds before checking again

        # Turn tracking off ???
        # No on!
        print("Turning tracking on...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.ON=ON\"")

        # Initialize the mount with geographic coordinates
        print("Setting the location...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.GEOGRAPHIC_COORDINATES.LATITUDE={self.latitude};LONGITUDE={self.longitude};ELEVATION={self.altitude}\"")

        # On coordinate set sync
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ON_COORDINATES_SET.SYNC=ON\"")
        
        # Sync the telescope with home coordinates
        print("Syncing the telescope with home coordinates...")
        home_az = 0.0
        home_alt = 45.0
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ={home_az};ALT={home_alt}\"")

        # Turn tracking back on
        print("Turning tracking back on...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.ON=ON\"")
        
        print("Mount initialization complete.")
        

if __name__ == "__main__":
    mount_control = MountControl()