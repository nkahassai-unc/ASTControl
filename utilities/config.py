# Configuration Settings

# REMOTE DEVICE INFO
RASPBERRY_PI_IP = "192.168.1.147"  # KC IP
SSH_USERNAME = "pi"
SSH_PASSWORD = "raspberry"

# WEATHER AND SOLAR DATA
DEFAULT_WEATHER_DATA = {
    "temperature": "--",
    "sky_conditions": "Unknown",
    "wind_speed": "--",
    "precip_chance": "--",
    "last_checked": None
}

DEFAULT_SOLAR_DATA = {
    "solar_alt": "--",
    "solar_az": "--",
    "sunrise": "--",
    "sunset": "--",
    "solar_noon": "--",
    "sun_time": "--"
}

# MOUNT COORDINATES
HOME_RA = "00:00:00"
HOME_DEC = "+00:00:00"

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
FILE_WATCH_DIR = "/home/pi/fc_files"

# Directory on the PC or Mac to copy files to (mounted via Samba, NFS, etc.)
FILE_DEST_DIR = "/Users/nathnaelkahassai/Documents/preprocess"

# Dictionary to track file statuses. Format: { "filename.avi": "Status" }
# Possible statuses: "Detected", "Copying", "Copied", "Failed"
FILE_STATUS = {}