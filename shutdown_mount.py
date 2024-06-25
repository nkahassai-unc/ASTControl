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

    def slew_home(self):
        """Stop mount tracking and slew back to the home position."""

        # Set the slew rate to maximum
        print("Setting slew rate to maximum...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.MAX=ON\"")
        
        # Slew back to the home position
        home_az = 0.0
        home_alt = 45.0
        print("Slewing back to the home position...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ={home_az};ALT={home_alt}\"")

        # Wait for the telescope to finish slewing
        while True:
            # Get the current Alt and Az
            current_az = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ\"")
            current_alt = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.ALT\"")

            # Parse the Alt and Az values from the command output
            try:
                current_az_value = float(current_az.split('=')[1])
                current_alt_value = float(current_alt.split('=')[1])
            except ValueError:
                print("Error parsing RA and DEC values.")
                return

            if abs(current_az_value - home_az) < 0.2 and abs(current_alt_value - home_alt) < 0.2:  # Assuming a small tolerance
                print("Mount is now at the home position.")
                #self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ABORT_MOTION.ABORT_MOTION=ON\"")
                #print("Motion aborted.")
                break
            else:
                print(f"Current AZ: {current_az_value}, Current ALT: {current_alt_value}. Waiting for mount to finish slewing...")
                time.sleep(5)  # Wait for 5 seconds before checking again

def main():
    mount_control = MountControl()
    mount_control.slew_home()

if __name__ == "__main__":
    main()