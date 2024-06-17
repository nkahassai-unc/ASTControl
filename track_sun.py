# Solar Tracking script to track the Sun using the mount simulator.

import time as pytime  # Renamed to avoid conflict with astropy's Time class
import subprocess
from astropy.coordinates import get_sun, EarthLocation
from astropy.time import Time
import astropy.units as u

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount Simulator'
        self.location = EarthLocation(lat=35.9132*u.deg, lon=-79.0558*u.deg, height=80*u.m)  # Chapel Hill, NC coordinates

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def get_sun_coordinates(self):
        """Fetch the current equatorial coordinates of the Sun."""
        now = Time.now()  # Current UTC time
        print("Current time:", now)
        sun = get_sun(now).transform_to('icrs')  # Get the Sun's position and transform to ICRS
        print("Sun position in ICRS:", sun)
        solar_ra = sun.ra.hour  # RA in hours
        solar_dec = sun.dec.deg  # Dec in degrees
        return solar_ra, solar_dec

    def track_sun(self):
        """Track the Sun by updating mount coordinates periodically."""
        solar_ra, solar_dec = self.get_sun_coordinates()
        print(f"Updating target coordinates to RA: {solar_ra}, Dec: {solar_dec}")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={solar_ra};DEC={solar_dec}\"")

        print("Slewing to the Sun and starting tracking...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ON_COORDINATES_SET.SLEW=ON\"")

        print("Mount is now tracking the Sun.")

def main():
    mount_control = MountControl()
    while True:
        mount_control.track_sun()
        pytime.sleep(30)  # Update every 30 seconds

if __name__ == "__main__":
    main()