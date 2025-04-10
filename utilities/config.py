# config.py

# Remote Device Info
RASPBERRY_PI_IP = "192.168.1.160"
SSH_USERNAME = "pi"
SSH_PASSWORD = "raspberry"

# API Keys
WEATHER_API_KEY = "10b2f1d4a200b534bb2d4bf69bddcace"
CITY = "Chapel Hill"

# DEFUALT DATA
DEFAULT_WEATHER_DATA = {
    "temperature": "--",
    "sky_conditions": "Unknown",
    "wind_speed": "--",
    "last_checked": None
}

DEFAULT_SOLAR_DATA = {
    "solar_alt": "--", "solar_az": "--", 
    "sunrise": "--", "sunset": "--", 
    "solar_noon": "--", "sun_time": None
}

# Arduino Shared State
ARDUINO_STATE = {
    "dome": "UNKNOWN",
    "etalon1": 90,
    "etalon2": 90,
    "last_updated": None
}

# Device Names
INDIGO_DEVICES = {
    "focuser": "Focuser #1",
    "etalon1": "Etalon #1",
    "etalon2": "Etalon #2",
}

# FireCapture Paths
FIRECAPTURE_EXE = "/path/to/FireCapture.sh"
SCREENSHOT_FOLDER = "/home/pi/fc_screens"

# Mount Coordinates (if needed)
HOME_RA = "00:00:00"
HOME_DEC = "+00:00:00"
