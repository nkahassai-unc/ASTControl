# Tracking script for mount control based on Sun position.

import time as pytime  # Renamed to avoid conflict with astropy's Time class
import subprocess
from astropy.coordinates import get_sun, EarthLocation, AltAz, SkyCoord, ICRS
from astropy.time import Time
import astropy.units as u

class MountControl:
    def __init__(self):
        """Initialize Mount & Location."""
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount PMC Eight'
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
        sun_gcrs = get_sun(now)
        altaz_frame = AltAz(obstime=now, location=self.location)
        sun_altaz = sun_gcrs.transform_to(altaz_frame)
        # Convert horizontal coordinates to equatorial coordinates (ICRS frame)
        equatorial_coord = sun_altaz.transform_to(ICRS) 
        sun_ra = equatorial_coord.ra.deg
        sun_dec = equatorial_coord.dec.deg
        return sun_ra, sun_dec

    def initial_slew(self):
        """Slew the telescope to the Sun and start tracking."""

        # On coordinate set track (slew to coordinates and start tracking)
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ON_COORDINATES_SET.TRACK=ON\"")
        
        # Set the slew rate to maximum
        print("Setting slew rate to maximum...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.MAX=ON\"")

        # Update the target coordinates
        solar_ra, solar_dec = self.get_sun_coordinates()
        print(f"Sun coordinates at RA: {solar_ra}, DEC: {solar_dec}")

        # Slew to the Sun and start tracking
        print("Slewing to the Sun.")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={solar_ra};DEC={solar_dec}\"")

        # Wait for the telescope to finish slewing
        while True:
            # Get the current RA and declination
            current_ra = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA\"")
            current_dec = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.DEC\"")

            # If the mount is within a small tolerance of the Sun's position, set the slew rate to guide
            if abs(current_ra - solar_ra) < 0.5 and abs(current_dec - solar_dec) < 0.5:
                print("Mount has finished slewing to the Sun.")
                
                # Set the slew rate to guide
                print("Setting slew rate to guide...")
                self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.GUIDE=ON\"")
                break
            else:
                print(f"Current RA: {current_ra}, Current Dec: {current_dec}. Waiting for mount to finish slewing...")
                pytime.sleep(3)  # Wait for 3 seconds before checking again

    def update_sun(self):
        """Track the Sun by updating mount coordinates periodically."""

        # Update the Solar coordinates
        solar_ra, solar_dec = self.get_sun_coordinates()
        print(f"Updating target coordinates to RA: {solar_ra}, Dec: {solar_dec}")

        # Slew to the updated coordinates
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={solar_ra};DEC={solar_dec}\"")

        # Get the current azimuth and altitude
        current_ra = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA\"")
        current_dec = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.DEC\"")

        # Assuming a small tolerance, check if the mount is on target
        if abs(current_ra - solar_ra) < 0.5 and abs(current_ra - solar_dec) < 0.5:
            print("Mount is on target.")
        else:
            print(f"Current RA: {current_ra}, Current Dec: {current_dec}. Waiting for mount to finish slewing...")
            print("Mount is not on target. Waiting for mount to finish slewing...")
            pytime.sleep(1)  # Wait for 1 seconds before checking again

        print("Mount position updated. Waiting for next update...")

def main():
    mount_control = MountControl()
    # Run initial_slew once to position the telescope towards the Sun initially
    mount_control.initial_slew()

    # After initial positioning, continuously update the Sun's position
    while True:
        mount_control.update_sun()
        pytime.sleep(10)  # Update every 10 seconds

if __name__ == "__main__":
    main()
