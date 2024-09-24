# Startup script to initialize the mount with location and home coordinates.

import subprocess
import time as pytime  # Renamed to avoid conflict with astropy's Time class
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
import astropy.units as u

class MountControl:
    def __init__(self, output_callback):
        """Mount & location settings."""
        self.mount_device = 'Mount PMC Eight'
        self.latitude = 35.913200  # N 
        self.longitude = 280.944153  # E 
        self.altitude = 80  # meters
        self.output_callback = output_callback  # Output callback function to send logs to app.py
        self.initialize_mount()

    def log(self, message):
        """Log output through the callback to app.py."""
        self.output_callback(f"{message}")

    def run_command(self, command):
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            self.log(f"Error executing command: {e.stderr.decode('utf-8')}")
            return None

    def get_home_coordinates(self):
        """Calculate home equatorial coordinates."""
        # Current UTC time
        now = Time.now()
        # Chapel Hill, NC coordinates
        self.location = EarthLocation(lat=35.9132 * u.deg, lon=-79.0558 * u.deg, height=80 * u.m)
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

    def initialize_mount(self):
        """Initalize mount."""
        # Connect the mount
        self.log("Connecting to the mount...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.CONNECTION.CONNECTED=ON\"")

        # Initialize the mount with geographic coordinates
        self.log("Setting the location...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.GEOGRAPHIC_COORDINATES.LATITUDE={self.latitude};LONGITUDE={self.longitude};ELEVATION={self.altitude}\"")

        # On coordinate set sync
        self.log("Setting on coordinate set sync...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_ON_COORDINATES_SET.SYNC=ON\"")

        # Set tracking to solar rate
        self.log("Setting tracking to solar rate...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACK_RATE.SOLAR=ON\"")

        # Turning tracking on
        self.log("Turning tracking on...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_TRACKING.ON=ON\"")
        self.run_command(f'indigo_prop_tool set "{self.mount_device}.MOUNT_TRACKING.OFF=OFF\"')

        # Calculate home coordinates
        home_ra, home_dec = self.get_home_coordinates()
        self.log(f"Home coordinates at RA: {home_ra}, DEC: {home_dec}")

        # Sync the telescope with home equatorial coordinates
        self.log("Syncing the telescope with home coordinates...")
        self.run_command(f"indigo_prop_tool set \"{self.mount_device}.MOUNT_EQUATORIAL_COORDINATES.RA={home_ra};DEC={home_dec}\"")

        self.log("Mount initialization complete.")
