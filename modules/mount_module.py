# Mount Module
# Mount control module using INDIGO JSON client

import threading
import time
from utilities.indigo_json_client import IndigoJSONClient
from modules.solar_module import SolarPosition

_socketio = None  # Module-level SocketIO reference

def set_socketio(instance):
    """Attach global socketio instance for emitting from MountControl."""
    global _socketio
    _socketio = instance


class MountControl:
    def __init__(self, indigo_client):
        self.client = indigo_client
        #self.device = "Mount PMC Eight"
        self.device = "Mount Simulator"

        self.solar = SolarPosition()
        self.set_location(35.9121, -79.0558, 100)  # Chapel Hill, NC
        self.tracking_active = False
        self.coord_monitor_active = False

        self.client.on("setNumberVector", self._handle_number_vector)
        self._start_coord_monitor()
        self.last_coords = {"ra": None, "dec": None}

    def emit_status(self, message):
        if _socketio:
            _socketio.emit("mount_status", message)

    def emit_log(self, message):
        if _socketio:
            _socketio.emit("server_log", f"[MOUNT_MODULE] {message}")

    def _handle_number_vector(self, msg):
        if msg.get("name") == "MOUNT_EQUATORIAL_COORDINATES":
            for item in msg.get("items", []):
                if item["name"] == "RA":
                    self.last_coords["ra"] = item["value"]
                elif item["name"] == "DEC":
                    self.last_coords["dec"] = item["value"]

            if _socketio:
                _socketio.emit("mount_coordinates", self.last_coords)

    def set_location(self, latitude, longitude, elevation):
        try:
            self.client.send({
                "newNumberVector": {
                    "device": self.device,
                    "name": "GEOGRAPHIC_COORDINATES",
                    "items": [
                        {"name": "LAT", "value": latitude},
                        {"name": "LONG", "value": longitude},
                        {"name": "ELEVATION", "value": elevation}
                    ]
                }
            }, quiet=True)
            self.emit_log(f"Set geographic coordinates: lat={latitude}, lon={longitude}, elev={elevation}")
        except Exception as e:
            self.emit_log(f"[ERROR] Failed to set location: {e}")
    
    def track_sun(self, interval=5):
        if self.tracking_active:
            self.emit_log("Sun tracking already active.")
            return

        self.tracking_active = True
        self.emit_status("Started Solar Tracking")

        def loop():
            while self.tracking_active:
                try:
                    self.solar.update_solar_position()
                    coords = self.solar.get_data()
                    if coords["solar_alt"] == "Below":
                        self.emit_status("Sun below horizon")
                    else:
                        ra, dec = self._get_equatorial_from_horizontal(
                            coords["solar_alt"], coords["solar_az"]
                        )
                        self._slew_to_coords(ra, dec)
                except Exception as e:
                    self.emit_log(f"Solar tracking failed: {e}")
                time.sleep(interval)

            self.emit_status("Stopped Solar Tracking")

        threading.Thread(target=loop, daemon=True).start()

    def stop_tracking(self):
        self.tracking_active = False

    def _get_equatorial_from_horizontal(self, alt, az):
        # Placeholder conversion
        return float(az), float(alt)

    def _slew_to_coords(self, ra, dec):
        try:
            self.client.send({
                "newNumberVector": {
                    "device": self.device,
                    "name": "MOUNT_EQUATORIAL_COORDINATES",
                    "items": [{"name": "RA", "value": ra}, {"name": "DEC", "value": dec}]
                }
            }, quiet=True)

            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_ON_COORDINATES_SET",  # Alternative: "MOUNT_TRACKING"
                    "items": [{"name": "ON_COORDINATES_SET", "value": True}]
                }
            }, quiet=True)

            self.emit_status(f"Slewing to RA: {ra}, DEC: {dec}")

        except Exception as e:
            self.emit_log(f"Slew to coords failed: {e}")

    def stop(self):
        self.emit_status("Stopping Mount")
        try:
            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_MOTION_DEC",
                    "items": [{"name": "NORTH", "value": False}, {"name": "SOUTH", "value": False}]
                }
            }, quiet=True)

            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_MOTION_RA",
                    "items": [{"name": "EAST", "value": False}, {"name": "WEST", "value": False}]
                }
            }, quiet=True)
            self.emit_log("Mount stopped successfully")

        except Exception as e:
            self.emit_log(f"Stop command failed: {e}")

    def park(self):
        self.emit_status("Parking Mount")
        self.stop_tracking()
        try:
            self._slew_to_coords(0.0, 90.0)
            time.sleep(5)
            self.stop()
        except Exception as e:
            self.emit_log(f"Park failed: {e}")

    def unpark(self):
        self.emit_status("Unparking Mount")
        # fix later
        try:
            # Slew to last known coordinates or a default position
            if self.last_coords["ra"] is not None and self.last_coords["dec"] is not None:
                self._slew_to_coords(self.last_coords["ra"], self.last_coords["dec"])
            else:
                self._slew_to_coords(0.0, 0.0)  # Default position if no coords available
        except Exception as e:
            self.emit_log(f"Unpark failed: {e}")

    def get_coordinates(self):
        return self.last_coords

    def _start_coord_monitor(self):
        self.coord_monitor_active = True

        def monitor():
            while self.coord_monitor_active:
                try:
                    self.client.send({
                        "getProperties": {
                            "device": self.device,
                            "name": "MOUNT_EQUATORIAL_COORDINATES"
                        }
                    }, quiet=True)
                except Exception as e:
                    self.emit_log(f"[ERROR] Coord monitor: {e}")
                time.sleep(1)

        threading.Thread(target=monitor, daemon=True).start()

    def shutdown(self):
        self.stop_tracking()
        self.coord_monitor_active = False
        self.client.close()
