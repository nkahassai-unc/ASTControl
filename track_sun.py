# Tracking script for mount control based on Sun position.

import time as pytime  # Renamed to avoid conflict with astropy's Time class
import subprocess
from astropy.coordinates import get_sun, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u

class MountControl:
    def __init__(self):
        self.indigo_server = 'localhost'
        self.mount_device = 'Mount SynScan'
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
        # print("Sun position in AltAz:", sun_altaz)
        solar_az = sun_altaz.az.deg  # Azimuth in degrees
        solar_alt = sun_altaz.alt.deg  # Altitude in degrees
        return solar_az, solar_alt

    def initial_slew(self):
        """Slew the telescope to the Sun and start tracking."""
        # On coordinate set slew
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ON_COORDINATES_SET.SLEW=ON\"")
        
        # Set the slew rate to maximum
        print("Setting slew rate to maximum...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.MAX=ON\"")

        # Update the target coordinates
        solar_az, solar_alt = self.get_sun_coordinates()
        print(f"Sun coordinates at Azimuth: {solar_az}, Altitude: {solar_alt}")

        # Slew to the Sun and start tracking
        print("Slewing to the Sun.")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ={solar_az};ALT={solar_alt}\"")

        # Wait for the telescope to finish slewing
        
        while True:
            # Get the current azimuth and altitude
            current_az_str = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ\"")
            current_alt_str = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.ALT\"")

            # Convert the current azimuth and altitude from string to float
            try:
                current_az = float(current_az_str)
                current_alt = float(current_alt_str)
            except ValueError:
                print(f"Error converting azimuth '{current_az_str}' or altitude '{current_alt_str}' to float.")
                break  # or continue, depending on desired error handling

            if abs(current_az - solar_az) < 0.5 and abs(current_alt - solar_alt) < 0.5:  # Assuming a small tolerance
                print("Mount has finished slewing to the Sun.")
                
                # Set the slew rate to guide
                print("Setting slew rate to guide...")
                self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_SLEW_RATE.GUIDE=ON\"")
                break
            else:
                print(f"Current Azimuth: {current_az}, Current Altitude: {current_alt}. Waiting for mount to finish slewing...")
                pytime.sleep(5)  # Wait for 5 seconds before checking again

    def update_sun(self):
        """Track the Sun by updating mount coordinates periodically."""

        # Update the Solar coordinates
        solar_az, solar_alt = self.get_sun_coordinates()
        print(f"Updating target coordinates to Azimuth: {solar_az}, Altitude: {solar_alt}")

        # Slew to the updated coordinates
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ={solar_az};ALT={solar_alt}\"")

        # Get the current azimuth and altitude
        current_az = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.AZ\"")
        current_alt = self.run_command(f"indigo_prop_tool get \"{self.mount_device}.MOUNT_HORIZONTAL_COORDINATES.ALT\"")

        if abs(current_az - solar_az) < 0.5 and abs(current_alt - solar_alt) < 0.5:  # Assuming a small tolerance
            print("Mount is on target.")
            
        else:
            print(f"Current Azimuth: {current_az}, Current Altitude: {current_alt}. Waiting for mount to finish slewing...")
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
        pytime.sleep(30)  # Update every 30 seconds

if __name__ == "__main__":
    main()
