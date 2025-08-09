# Mount Module
# Mount control module using INDIGO JSON client

import threading
import time
import ephem
from modules.astro_module import AstroPosition
from utilities import config
from utilities.config import (
    GEO_LAT, GEO_LON, GEO_ELEV,
    HOME_RA, HOME_DEC, PARK_RA, PARK_DEC,
    LOCATION_PROFILES,
)
from utilities.logger import emit_log

_socketio = None  # Module-level SocketIO reference

def set_socketio(instance):
    """Attach global socketio instance for emitting from MountControl."""
    global _socketio
    _socketio = instance


class MountControl:
    def __init__(self, indigo_client):
        """Initialize MountControl with INDIGO client."""
        self.client = indigo_client
        self.device = "Mount Agent"

        # --- State ---
        self.location_profile = "chapel_hill"  # default profile
        self.target_mode = "sun"               # "sun" | "moon"

        # Observer used for transforms
        self.observer = ephem.Observer()
        self.observer.lat = str(GEO_LAT)
        self.observer.lon = str(GEO_LON)
        self.observer.elev = GEO_ELEV

        # Astro helper (Sun + Moon)
        self.astro = AstroPosition(GEO_LAT, GEO_LON)

        # Send site to mount controller
        self.set_location(GEO_LAT, GEO_LON, GEO_ELEV)

        # Run-time flags/state
        self.tracking_active = False
        self.coord_monitor_active = False
        self.last_coords = {"ra": None, "dec": None}
        self.last_ra = config.LAST_RA
        self.last_dec = config.LAST_DEC
        self.park_status = config.MOUNT_PARKED
        self.mount_connected = False

        # INDIGO event hook + background coord poller
        self.client.on("setNumberVector", self._handle_number_vector)
        self._start_coord_monitor()

    # ----------------- Emits / Logging -----------------
    def emit_status(self, message):
        """Emit mount status + context to frontend and logger."""
        if _socketio:
            # Normalize RA/Dec from astro based on target
            eq = self.astro.get_equatorial(self.target_mode) or {}
            ra_key = "ra_moon" if self.target_mode == "moon" else "ra_solar"
            dec_key = "dec_moon" if self.target_mode == "moon" else "dec_solar"
            target_ra_str = eq.get(ra_key, "--:--:--")
            target_dec_str = eq.get(dec_key, "--:--:--")

            # Current mount coords (floats in hours/degs)
            mc = self.get_coordinates()
            mount_ra_f = mc.get("ra")
            mount_dec_f = mc.get("dec")

            _socketio.emit("mount_status", {
                "status": message,
                "target": self.target_mode,
                "location": self.location_profile,
                "target_ra": target_ra_str,
                "target_dec": target_dec_str,
                "mount_ra": mount_ra_f,
                "mount_dec": mount_dec_f,
                "mount_ra_str": self.format_ra(mount_ra_f) if mount_ra_f is not None else "--:--:--",
                "mount_dec_str": self.format_dec(mount_dec_f) if mount_dec_f is not None else "--:--:--",
            })

            # Optional: push astro snapshot so UI solar/lunar panel updates instantly
            if hasattr(self.astro, "get_data"):
                _socketio.emit("astro_update", self.astro.get_data())

        emit_log(f"[STATUS] {message}")
        self._last_status = message

    def emit_log(self, message):
        """Emit log message to frontend and logger."""
        if _socketio:
            _socketio.emit("server_log", f"[MOUNT_MODULE] {message}")
        emit_log(message)

    # ----------------- Formatting helpers -----------------
    def format_ra(self, ra):
        """Format RA (hours float) to HH:MM:SS."""
        hours = int(ra)
        minutes = int((ra - hours) * 60)
        seconds = (ra - hours - minutes / 60) * 3600
        return f"{hours:02}:{minutes:02}:{seconds:05.2f}"

    def format_dec(self, dec):
        """Format DEC (deg float) to ±DD:MM:SS."""
        sign = "-" if dec < 0 else "+"
        dec = abs(dec)
        degrees = int(dec)
        minutes = int((dec - degrees) * 60)
        seconds = (dec - degrees - minutes / 60) * 3600
        return f"{sign}{degrees:02}:{minutes:02}:{seconds:05.2f}"

    # ----------------- Astro / transforms -----------------
    def compute_altaz(self):
        """Compute current Alt/Az from last known RA/DEC and emit via SocketIO."""
        try:
            self.observer.date = ephem.now()
            mount_ra = self.last_coords["ra"]
            mount_dec = self.last_coords["dec"]
            if mount_ra is None or mount_dec is None:
                return None

            radec = ephem.Equatorial(mount_ra * 15, mount_dec)  # RA given in *hours* → degrees
            mount = ephem.FixedBody()
            mount._ra = radec.ra
            mount._dec = radec.dec
            mount.compute(self.observer)

            alt_deg = float(mount.alt) * 180 / ephem.pi
            az_deg = float(mount.az) * 180 / ephem.pi

            if _socketio:
                _socketio.emit("mount_altaz", {"alt": round(alt_deg, 2), "az": round(az_deg, 2)})

            return alt_deg, az_deg

        except Exception as e:
            emit_log(f"[ERROR] Alt/Az computation failed: {e}")
            return None

    # ----------------- INDIGO event intake -----------------
    def _handle_number_vector(self, msg):
        """Handle incoming NumberVector messages from INDIGO."""
        if msg.get("name") == "MOUNT_EQUATORIAL_COORDINATES":
            for item in msg.get("items", []):
                if item["name"] == "RA":
                    self.last_coords["ra"] = item["value"]
                    config.LAST_RA = item["value"]
                elif item["name"] == "DEC":
                    self.last_coords["dec"] = item["value"]
                    config.LAST_DEC = item["value"]

            if _socketio:
                _socketio.emit("mount_coordinates", {
                    "ra": self.last_coords["ra"],
                    "dec": self.last_coords["dec"],
                    "ra_str": self.format_ra(self.last_coords["ra"]) if self.last_coords["ra"] is not None else "--:--:--",
                    "dec_str": self.format_dec(self.last_coords["dec"]) if self.last_coords["dec"] is not None else "--:--:--",
                })

            self.compute_altaz()
            emit_log(f"[MOUNT] Updated coordinates: RA={self.last_coords['ra']}, DEC={self.last_coords['dec']}")

    # ----------------- Site / profile control -----------------
    def _resolve_profile(self, profile_name):
        """Return (lat, lon, elev) from LOCATION_PROFILES; supports dict or tuple entries."""
        prof = LOCATION_PROFILES.get(profile_name)
        if isinstance(prof, dict):
            return float(prof.get("lat", GEO_LAT)), float(prof.get("lon", GEO_LON)), float(prof.get("elev", GEO_ELEV))
        if isinstance(prof, (list, tuple)) and len(prof) >= 3:
            lat, lon, elev = prof[:3]
            return float(lat), float(lon), float(elev)
        # fallback to current site
        return float(GEO_LAT), float(GEO_LON), float(GEO_ELEV)

    def set_location(self, latitude, longitude, elevation):
        """Send geographic coordinates to mount agent (INDIGO)."""
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

    def set_location_profile(self, profile_name):
        """Switch observer/location to a preset profile."""
        if profile_name not in LOCATION_PROFILES:
            self.emit_log(f"[ERROR] Unknown location profile: {profile_name}")
            return

        lat, lon, elev = self._resolve_profile(profile_name)

        # Update local observer
        self.observer.lat = str(lat)
        self.observer.lon = str(lon)
        self.observer.elev = elev

        # Update INDIGO + astro module observer
        self.set_location(lat, lon, elev)
        if hasattr(self.astro, "set_observer"):
            self.astro.set_observer(lat, lon, elev)

        self.location_profile = profile_name
        self.emit_status(f"Location set: {profile_name.replace('_',' ').title()}")

    def toggle_location_profile(self):
        """Toggle between Chapel Hill and Kansas City."""
        new_profile = "kansas_city" if self.location_profile == "chapel_hill" else "chapel_hill"
        self.set_location_profile(new_profile)

    # ----------------- Target control -----------------
    def set_target(self, mode):
        """Set target to 'sun' or 'moon'."""
        m = str(mode).lower()
        if m not in ("sun", "moon"):
            self.emit_log(f"[ERROR] Unknown target: {mode}")
            return
        self.target_mode = m
        self.emit_status(f"Target set: {m.title()}")

    def toggle_target(self):
        """Toggle observing target between Sun and Moon."""
        self.set_target("moon" if self.target_mode == "sun" else "sun")

    # ----------------- Motion / tracking -----------------
    def slew(self, direction, rate="solar"):
        """Slew the mount in a cardinal direction at specified rate."""
        self.emit_status(f"Slewing {direction.title()} ({rate.title()})")

        rate_map = {
            "slow": "GUIDE",
            "fast": "MAX",
            "solar": "CENTERING",  # light movement mode
        }

        # Apply tracking ON for solar mode
        if rate == "solar":
            self.client.send({
                "newSwitchVector": {
                    "device": self.device,
                    "name": "MOUNT_TRACKING",
                    "items": [{"name": "ON", "value": True}, {"name": "OFF", "value": False}]
                }
            }, quiet=True)

        # Send slew rate
        selected_rate = rate_map.get(rate.lower(), "CENTERING")
        self.client.send({
            "newSwitchVector": {
                "device": self.device,
                "name": "MOUNT_SLEW_RATE",
                "items": [{"name": selected_rate, "value": True}]
            }
        }, quiet=True)

        # Motion vectors
        ra_vector, dec_vector = [], []
        if direction == "north":
            dec_vector = [{"name": "NORTH", "value": True}, {"name": "SOUTH", "value": False}]
        elif direction == "south":
            dec_vector = [{"name": "NORTH", "value": False}, {"name": "SOUTH", "value": True}]
        elif direction == "east":
            ra_vector = [{"name": "EAST", "value": True}, {"name": "WEST", "value": False}]
        elif direction == "west":
            ra_vector = [{"name": "EAST", "value": False}, {"name": "WEST", "value": True}]
        else:
            self.emit_log(f"[ERROR] Invalid slew direction: {direction}")
            return

        if ra_vector:
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_MOTION_RA", "items": ra_vector}}, quiet=True)
        if dec_vector:
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_MOTION_DEC", "items": dec_vector}}, quiet=True)

    def stop(self):
        """Stop all mount motion."""
        try:
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_MOTION_DEC",
                                                  "items": [{"name": "NORTH", "value": False}, {"name": "SOUTH", "value": False}]}}, quiet=True)
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_MOTION_RA",
                                                  "items": [{"name": "EAST", "value": False}, {"name": "WEST", "value": False}]}}, quiet=True)

            self.emit_status("Stopped")
            time.sleep(0.5)
            self.emit_status("Idle")
            self.emit_log("[MOUNT] Mount stopped successfully")

        except Exception as e:
            self.emit_log(f"[MOUNT] Stop command failed: {e}")

    def _slew_to_coords(self, ra, dec):
        """Slew to specified RA/DEC coordinates (floats: RA hours, DEC degrees)."""
        try:
            self.client.send({"newNumberVector": {"device": self.device, "name": "MOUNT_EQUATORIAL_COORDINATES",
                                                  "items": [{"name": "RA", "value": ra}, {"name": "DEC", "value": dec}]}}, quiet=True)
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_ON_COORDINATES_SET",
                                                  "items": [{"name": "ON_COORDINATES_SET", "value": True}]}}, quiet=True)
            self.emit_log(f"[MOUNT] Slewing to RA: {ra}, DEC: {dec}")
        except Exception as e:
            self.emit_log(f"[MOUNT] Slew to coords failed: {e}")

    def park(self):
        """Slew to park position and disable tracking."""
        self.emit_status("Parking...")
        self.stop_tracking()
        try:
            self._slew_to_coords(PARK_RA, PARK_DEC)
            # Poll until near park
            for _ in range(10):
                coords = self.get_coordinates()
                ra, dec = coords["ra"], coords["dec"]
                if ra is not None and dec is not None:
                    if abs(ra - PARK_RA) < 0.01 and abs(dec - PARK_DEC) < 0.01:
                        break
                time.sleep(1)
            self.stop()
            self.emit_status("Parked")
            self.emit_log("[MOUNT] Park complete")
        except Exception as e:
            self.emit_log(f"[ERROR] Park failed: {e}")

    def unpark(self):
        """Slew back to last known coordinates or home position if none."""
        self.emit_status("Unparking...")
        try:
            ra = self.last_coords["ra"] if self.last_coords["ra"] is not None else self._parse_ra(HOME_RA)
            dec = self.last_coords["dec"] if self.last_coords["dec"] is not None else self._parse_dec(HOME_DEC)
            self._slew_to_coords(ra, dec)
            self.emit_status("Unparked")
            self.emit_log("[MOUNT] Unpark complete")
        except Exception as e:
            self.emit_log(f"[ERROR] Unpark failed: {e}")
            self.emit_status("Unparked failed")

    def _parse_ra(self, ra_str):
        """Parse RA string in HH:MM:SS → decimal hours."""
        h, m, s = map(float, ra_str.split(":"))
        return h + m / 60 + s / 3600

    def _parse_dec(self, dec_str):
        """Parse DEC string in ±DD:MM:SS → decimal degrees."""
        sign = -1 if dec_str.startswith("-") else 1
        parts = list(map(float, dec_str.strip("+-").split(":")))
        return sign * (parts[0] + parts[1] / 60 + parts[2] / 3600)

    def stop_tracking(self):
        """Disable mount tracking."""
        self.tracking_active = False
        try:
            self.client.send({"newSwitchVector": {"device": self.device, "name": "MOUNT_TRACKING",
                                                  "items": [{"name": "OFF", "value": True}, {"name": "ON", "value": False}]}}, quiet=True)
            self.emit_log("[MOUNT] Tracking disabled")
            self.emit_status("Tracking disabled")
        except Exception as e:
            self.emit_log(f"[ERROR] Failed to disable tracking: {e}")
            self.emit_status("Tracking disable failed")

    def get_coordinates(self, emit=False):
        """Return last known RA/DEC (floats). Optionally emit formatted strings."""
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
        """Start background thread to poll mount coordinates every second."""
        self.coord_monitor_active = True

        def monitor():
            while self.coord_monitor_active:
                try:
                    self.client.send({"getProperties": {"device": self.device, "name": "MOUNT_EQUATORIAL_COORDINATES"}}, quiet=True)
                except Exception as e:
                    emit_log(f"[ERROR] Coord monitor: {e}")
                time.sleep(1)

        threading.Thread(target=monitor, daemon=True).start()

    def shutdown(self):
        """Clean up on application exit."""
        self.stop_tracking()
        self.coord_monitor_active = False
        self.client.close()