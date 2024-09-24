# Shutdown script for mount tracking and slews back to the home position.

import time as pytime  # Renamed to avoid conflict with astropy's Time class
import subprocess
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
import astropy.units as u

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount PMC Eight'

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8').strip()}")
            return None

    def get_home_coordinates(self):
        """Calculate home equatorial coordinates."""
        now = Time.now()  # Current UTC time
        # Chapel Hill, NC coordinates
        self.location = EarthLocation(lat=35.9132*u.deg, lon=-79.0558*u.deg, height=80*u.m)
        # Define the AltAz frame for the given time and location
        altaz_frame = AltAz(obstime=now, location=self.location)

        # Due west azimuth is 270 degrees, and horizon altitude is 0 degrees
        az = 270 * u.deg
        alt = 0 * u.deg

        # Create a SkyCoord object for the given alt/az
        horizontal_coord = SkyCoord(alt=alt, az=az, frame=altaz_frame)
        # Convert horizontal coordinates to equatorial coordinates (ICRS frame)
        equatorial_coord = horizontal_coord.transform_to(ICRS) 
        home_ra = equatorial_coord.ra.deg
        home_dec = equatorial_coord.dec.deg
        return home_ra, home_dec

    def slew_home(self):
        """Stop mount tracking and slew back to the home position."""

        # Set the slew rate to maximum
        print("Setting slew rate to maximum...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.MAX=ON\"")
        
        # Slew back to the home position
        home_ra, home_dec = self.get_home_coordinates()
        print("Slewing back to the home position...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={home_ra};DEC={home_dec}\"")

        # Wait for the telescope to finish slewing
        while True:
            # Get the current RA and Declination
            current_ra = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA\"")
            current_dec = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.DEC\"")

            # Check if the mount is at the home position
            if abs(current_ra - home_ra) < 0.2 and abs(current_dec - home_dec) < 0.2:
                print("Mount is now at the home position.")
                #self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ABORT_MOTION.ABORT_MOTION=ON\"")
                #print("Motion aborted.")
                self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.ON=OFF\"")
                self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.OFF=ON\"")
                print("Tracking stopped.")
                break
            else:
                print(f"Current RA: {current_ra}, Current DEC: {current_dec}. Waiting for mount to finish slewing...")
                pytime.sleep(3)  # Wait for 3 seconds before checking again

    def close_dome(self):
        """Close the dome."""
        print("Closing the dome...")
        # insert arduino scripting here
        #self.run_command(f"indigo_prop_tool set \"Dome Simulator.DOME_SHUTTER.CLOSE=ON\""

def main():
    mount_control = MountControl()
    mount_control.slew_home()

if __name__ == "__main__":
    main()