# Shutdown script for Indigo Astronomy Software
# Stops mount tracking and slews back to the home position.

import time
import subprocess

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount SynScan'

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8').strip()}")
            return None

    def stop_tracking_and_slew_home(self):
        """Stop mount tracking and slew back to the home position."""

        # Stop tracking
        print("Stopping tracking...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.OFF=ON\"")

        # Set the slew rate to maximum
        print("Setting slew rate to maximum...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.MAX=ON\"")
        
        # Slew back to the home position
        home_ra = 0.0
        home_dec = 90.0
        print("Slewing back to the home position...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={home_ra};DEC={home_dec}\"")

        # Wait for the mount to move to the home position
        time.sleep(5)  # Adjust the sleep time as necessary

        # Check if the mount is at the home position by getting RA and DEC separately
        current_ra = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA\"")
        current_dec = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.DEC\"")
        
        # Parse the RA and DEC values from the command output
        # Assuming the output format is "RA=<value>" and "DEC=<value>"
        try:
            current_ra_value = float(current_ra)
            current_dec_value = float(current_dec)
        except ValueError:
            print("Error parsing RA and DEC values.")
            return

        if abs(current_ra_value - home_ra) < 0.2 and abs(current_dec_value - home_dec) < 0.2:  # Assuming a small tolerance
            print("Mount is now at the home position.")
            self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ABORT_MOTION.ABORT_MOTION=ON\"")
            print("Motion aborted.")
        else:
            print("Mount has not reached the home position yet.")

def main():
    mount_control = MountControl()
    mount_control.stop_tracking_and_slew_home()

if __name__ == "__main__":
    main()