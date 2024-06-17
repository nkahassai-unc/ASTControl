# Shutdown script for Indigo Astronomy Software
# Stops mount tracking and slews back to the home position.

import subprocess

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount Simulator'

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def stop_tracking_and_slew_home(self):
        """Stop mount tracking and slew back to the home position."""
        print("Stopping tracking...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.OFF=ON\"")
        
        home_ra = 0.0
        home_dec = 90.0
        print("Slewing back to the home position...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={home_ra};DEC={home_dec}\"")

        print("Mount is now at the home position.")

def main():
    mount_control = MountControl()
    mount_control.stop_tracking_and_slew_home()

if __name__ == "__main__":
    main()