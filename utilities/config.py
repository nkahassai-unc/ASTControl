# Confguration Settings

# Remote Device Info
RASPBERRY_PI_IP = "192.168.1.160"
SSH_USERNAME = "pi"
SSH_PASSWORD = "raspberry"

# DEFAULT DATA
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

# Arduino Shared State
ARDUINO_STATE = {
    "dome": "UNKNOWN",
    "etalon1": 90,
    "etalon2": 90,
    "last_updated": None
}

# FireCapture Paths
FIRECAPTURE_EXE = "/path/to/FireCapture.sh"
SCREENSHOT_FOLDER = "/home/pi/fc_screens"

# Mount Coordinates (if needed)
HOME_RA = "00:00:00"
HOME_DEC = "+00:00:00"
