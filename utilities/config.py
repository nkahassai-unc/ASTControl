# Configuration Settings

# REMOTE DEVICE INFO
RASPBERRY_PI_IP = "192.168.1.147"  # KC IP
SSH_USERNAME = "pi"
SSH_PASSWORD = "raspberry"

# DEFAULT GEOGRAPHIC COORDINATES (Chapel Hill, NC)
GEO_LAT  = 35.9132
GEO_LON  = -79.0558
GEO_ELEV = 148  # m

# LOCATION PROFILES
LOCATION_PROFILES = {
    "chapel_hill": {"lat": 35.9132, "lon": -79.0558, "elev": 148, "tz": "America/New_York"},
    "kansas_city": {"lat": 39.0997, "lon": -94.5786, "elev": 270, "tz": "America/Chicago"},
}

# WEATHER DATA
DEFAULT_WEATHER_DATA = {
    "temperature": "--",
    "sky_conditions": "Unknown",
    "wind_speed": "--",
    "precip_chance": "--",
    "last_checked": None
}

# SOLAR DATA
DEFAULT_SOLAR_DATA = {
    "solar_alt": "--",
    "solar_az": "--",
    "sunrise": "--",
    "sunset": "--",
    "solar_noon": "--",
    "sun_time": "--"
}

solar_cache = {
    "date_sun": None,
    "path_sun": None,
    "date_moon": None,
    "path_moon": None
}

# MOUNT COORDINATES
HOME_RA = "00:00:00"
HOME_DEC = "+00:00:00"
MOUNT_PARKED = None  # Assume nothing at start
PARK_RA = 0.0
PARK_DEC = 90.0
LAST_RA = None
LAST_DEC = None

# ARDUINO SHARED STATE
ARDUINO_STATE = {
    "dome": "UNKNOWN",
    "etalon1": 90,
    "etalon2": 90,
    "last_updated": None,
    "connected": False  # new flag
}

# FIRECAPTURE PATHS
FIRECAPTURE_EXE = "/path/to/FireCapture.sh"
SCREENSHOT_FOLDER = "/home/pi/fc_screens"

# === FILE HANDLER CONFIG ===
# Directory on the Pi to watch for new video files (e.g., Samba-shared)
FILE_WATCH_DIR = "fc_files"
FILE_WATCH_LOCAL_PATH = "/home/pi/fc_files"

# Directory on the PC or Mac to copy files to (mounted via Samba, NFS, etc.)
FILE_DEST_DIR = "/Users/nathnaelkahassai/Documents/preprocess"

# Dictionary to track file statuses. Format: { "filename.avi": "Status" }
# Possible statuses: "Detected", "Copying", "Copied", "Failed"
FILE_STATUS = {}