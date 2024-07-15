# Cross reference calculations for telescope coordinates

from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, ICRS, SkyCoord
import astropy.units as u

# Observer's location (Chapel Hill, NC)
location = EarthLocation(lat=35.9132*u.deg, lon=-79.0558*u.deg, height=80*u.m)

# Current time
now = Time.now()

# RA and Dec of the object
ra = 1.554 * u.deg
dec = 90 * u.deg

# Create SkyCoord object for the given RA and Dec
icrs_coord = SkyCoord(ra=ra, dec=dec, frame='icrs')

# Define the AltAz frame
altaz_frame = AltAz(obstime=now, location=location)

# Convert to AltAz coordinates
altaz_coord = icrs_coord.transform_to(altaz_frame)

# Extract Altitude and Azimuth
altitude = altaz_coord.alt
azimuth = altaz_coord.az

print(f"Altitude: {altitude.deg} degrees")
print(f"Azimuth: {azimuth.deg} degrees")
print("polaris")

# Test home positions
"""Calculate home equatorial coordinates."""
# Due west azimuth is 270 degrees, and horizon altitude is 0 degrees
az = 270 * u.deg
alt = 0 * u.deg
# Create a SkyCoord object for the given alt/az
horizontal_coord = SkyCoord(alt=alt, az=az, frame=altaz_frame)

# Convert horizontal coordinates to equatorial coordinates (ICRS frame)
equatorial_coord = horizontal_coord.transform_to(ICRS) 
home_ra = equatorial_coord.ra.deg
home_dec = equatorial_coord.dec.deg
print(f"RA: {home_ra} degrees, Dec: {home_dec} degrees")
print("home")