# Tracking script for mount control based on Sun position.

import time as pytime  # Renamed to avoid conflict with astropy's Time class
import subprocess
from astropy.coordinates import get_sun, EarthLocation, AltAz
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
        sun = get_sun(now)
        altaz_frame = AltAz(obstime=now, location=self.location)
        sun_altaz = sun.transform_to(altaz_frame)
        print("Sun position in AltAz:", sun_altaz)
        solar_az = sun_altaz.az.deg  # Azimuth in degrees
        solar_alt = sun_altaz.alt.deg  # Altitude in degrees
        return solar_az, solar_alt

    def track_sun(self):
        """Track the Sun by updating mount coordinates periodically."""
        solar_az, solar_alt = self.get_sun_coordinates()
        print(f"Updating target coordinates to Azimuth: {solar_az}, Altitude: {solar_alt}")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.AZ={solar_az};ALT={solar_alt}\"")

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
