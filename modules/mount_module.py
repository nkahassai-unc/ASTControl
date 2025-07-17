# Mount Module
# Mount control module using INDIGO JSON client

import threading
import time
from utilities.indigo_json_client import IndigoJSONClient
from modules.solar_module import SolarPosition
from utilities.config import GEO_LAT, GEO_LON, GEO_ELEV, HOME_RA, HOME_DEC, MOUNT_PARKED
from utilities.logger import emit_log

_socketio = None  # Module-level SocketIO reference

def set_socketio(instance):
    """Attach global socketio instance for emitting from MountControl."""
    global _socketio
    _socketio = instance


class MountControl:
    def __init__(self, indigo_client):
        self.client = indigo_client
        #self.device = "Mount PMC Eight"
        #self.device = "Mount Simulator"
        self.device = "Mount Agent"

        self.solar = SolarPosition()
        self.set_location(GEO_LAT, GEO_LON, GEO_ELEV)
        self.tracking_active = False
        self.coord_monitor_active = False

        self.client.on("setNumberVector", self._handle_number_vector)
        self._start_coord_monitor()
        self.last_coords = {"ra": None, "dec": None}

    def emit_status(self, message):
        if _socketio:
            _socketio.emit("mount_status", message)
        emit_log(f"[STATUS] {message}")

    def emit_log(self, message):
        if _socketio:
            _socketio.emit("server_log", f"[MOUNT_MODULE] {message}")
        emit_log(message)

    def _handle_number_vector(self, msg):
        if msg.get("name") == "MOUNT_EQUATORIAL_COORDINATES":
            for item in msg.get("items", []):
                if item["name"] == "RA":
                    self.last_coords["ra"] = item["value"]
                elif item["name"] == "DEC":
                    self.last_coords["dec"] = item["value"]

            if _socketio:
                _socketio.emit("mount_coordinates", {
                    "ra": self.last_coords["ra"],
                    "dec": self.last_coords["dec"],
                    "ra_str": self.format_ra(self.last_coords["ra"]),
                    "dec_str": self.format_dec(self.last_coords["dec"]),
                })

    def format_ra(self, ra):
        """Convert RA in decimal hours to HH:MM:SS.ss format."""
        hours = int(ra)
        minutes = int((ra - hours) * 60)
        seconds = (ra - hours - minutes / 60) * 3600
        return f"{hours:02}:{minutes:02}:{seconds:05.2f}"

    def format_dec(self, dec):
        """Convert DEC in decimal degrees to ±DD:MM:SS.ss format."""
        sign = "-" if dec < 0 else "+"
        dec = abs(dec)
        degrees = int(dec)
        minutes = int((dec - degrees) * 60)
        seconds = (dec - degrees - minutes / 60) * 3600
        return f"{sign}{degrees:02}:{minutes:02}:{seconds:05.2f}"

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
            emit_log(f"[MOUNT] Set geographic coordinates: lat={latitude}, lon={longitude}, elev={elevation}")
        except Exception as e:
            emit_log(f"[ERROR] Failed to set location: {e}")

    def slew(self, direction, rate="solar"):
        emit_log(f"[MOUNT] Slewing {direction.upper()} ({rate} rate)")

        ra_vector = []
        dec_vector = []

        if direction == "north":
            dec_vector = [{"name": "NORTH", "value": True}, {"name": "SOUTH", "value": False}]
        elif direction == "south":
            dec_vector = [{"name": "NORTH", "value": False}, {"name": "SOUTH", "value": True}]
        elif direction == "east":
            ra_vector = [{"name": "EAST", "value": True}, {"name": "WEST", "value": False}]
        elif direction == "west":
            ra_vector = [{"name": "EAST", "value": False}, {"name": "WEST", "value": True}]
        else:
            emit_log(f"[ERROR] Invalid slew direction: {direction}")
            return

        if ra_vector:
            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_MOTION_RA",
                    "items": ra_vector
                }
            }, quiet=True)

        if dec_vector:
            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_MOTION_DEC",
                    "items": dec_vector
                }
            }, quiet=True)

        slew_rate = 1.0 if rate == "solar" else 0.5 if rate == "slow" else 2.0
        self.client.send({
            "newNumberVector": {
                "device": self.device,
                "name": "MOUNT_SLEW_RATE",
                "items": [{"name": "SLEW_RATE", "value": slew_rate}]
            }
        }, quiet=True)

    def stop_tracking(self):
        self.tracking_active = False

    def _get_equatorial_from_horizontal(self, alt, az):
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
                    "name": "MOUNT_ON_COORDINATES_SET",
                    "items": [{"name": "ON_COORDINATES_SET", "value": True}]
                }
            }, quiet=True)

            emit_log(f"[MOUNT] Slewing to RA: {ra}, DEC: {dec}")

        except Exception as e:
            emit_log(f"[MOUNT] Slew to coords failed: {e}")

    def stop(self):
        emit_log("[MOUNT] Stopping Mount")
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
            emit_log("[MOUNT] Mount stopped successfully")

        except Exception as e:
            emit_log(f"[MOUNT] Stop command failed: {e}")

    def park(self):
        emit_log("[MOUNT] Parking Mount")
        self.stop_tracking()
        try:
            self._slew_to_coords(0.0, 90.0)
            time.sleep(5)
            self.stop()
        except Exception as e:
            emit_log(f"Park failed: {e}")

    def unpark(self):
        emit_log("[MOUNT] Unparking Mount")
        try:
            if self.last_coords["ra"] is not None and self.last_coords["dec"] is not None:
                self._slew_to_coords(self.last_coords["ra"], self.last_coords["dec"])
            else:
                self._slew_to_coords(0.0, 0.0)
        except Exception as e:
            emit_log(f"[MOUNT] Unpark failed: {e}")

    def get_coordinates(self, emit=False):
        if emit and _socketio:
            ra = self.last_coords["ra"]
            dec = self.last_coords["dec"]
            _socketio.emit("mount_coordinates", {
                "ra": ra,
                "dec": dec,
                "ra_str": self.format_ra(ra) if ra is not None else "--:--:--",
                "dec_str": self.format_dec(dec) if dec is not None else "--:--:--",
            })
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
                    emit_log(f"[ERROR] Coord monitor: {e}")
                time.sleep(1)

        threading.Thread(target=monitor, daemon=True).start()

    def shutdown(self):
        self.stop_tracking()
        self.coord_monitor_active = False
        self.client.close()