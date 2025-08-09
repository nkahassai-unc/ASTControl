# Astro Module
# Combined solar and lunar position module using PyEphem

import threading
import ephem
from datetime import datetime, timedelta, timezone
from utilities.config import GEO_LAT, GEO_LON, GEO_ELEV, solar_cache
from utilities.logger import emit_log

_socketio = None

def set_socketio(sio):
    global _socketio
    _socketio = sio


class AstroPosition:
    """
    Solar + Lunar position service.
    - target_mode: "sun" | "moon" (used to map payload to the front-end keys you already bind)
    - location_profile: optional label string ("chapel_hill"/"kansas_city") for UI display only
    """
    def __init__(self, latitude=GEO_LAT, longitude=GEO_LON, elevation=GEO_ELEV):
        self._lock = threading.Lock()

        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.elevation = float(elevation)

        self.observer = ephem.Observer()
        self.observer.lat = str(self.latitude)
        self.observer.lon = str(self.longitude)
        self.observer.elev = self.elevation

        # Local tz is not strictly needed since ephem.localtime returns localtime,
        # but keep a handle if you want formatting later.
        self.local_tz = timezone(timedelta(hours=-5))

        # public flags/UI hints
        self.target_mode = "sun"            # "sun" or "moon"
        self.location_profile = None        # "chapel_hill"/"kansas_city" for display only

        # State caches for quick emits
        self.sun_times   = {"sunrise": "--", "sunset": "--", "solar_noon": "--"}
        self.sun_pos     = {"solar_alt": "--", "solar_az": "--", "sun_time": "--"}

        self.moon_times  = {"moonrise": "--", "moonset": "--", "moon_transit": "--"}
        self.moon_pos    = {"lunar_alt": "--", "lunar_az": "--", "moon_time": "--"}

        # Prime values
        self.update_sun_times()
        self.update_moon_times()
        self.update_solar_position()
        self.update_lunar_position()

    # ---------------- Location / Target control ----------------

    def set_observer(self, lat, lon, elev=None):
        """Update observer coordinates."""
        with self._lock:
            self.latitude = float(lat)
            self.longitude = float(lon)
            if elev is not None:
                self.elevation = float(elev)
            self.observer.lat = str(self.latitude)
            self.observer.lon = str(self.longitude)
            self.observer.elev = self.elevation
            self.clear_path_cache()

    def set_target_mode(self, mode: str):
        """Set active target (sun|moon)."""
        mode = (mode or "sun").lower()
        self.target_mode = "moon" if mode == "moon" else "sun"

    def set_location_profile_label(self, profile: str):
        """Optional label so the UI can show the profile name."""
        self.location_profile = profile

    # ---------------- Solar ----------------

    def update_sun_times(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                sunrise = ephem.localtime(self.observer.next_rising(ephem.Sun()))
                sunset  = ephem.localtime(self.observer.next_setting(ephem.Sun()))
                transit = ephem.localtime(self.observer.next_transit(ephem.Sun()))
            self.sun_times.update({
                "sunrise": sunrise.strftime("%H:%M"),
                "sunset": sunset.strftime("%H:%M"),
                "solar_noon": transit.strftime("%H:%M"),
            })
        except Exception as e:
            emit_log(f"[SOLAR] Times error: {e}")

    def update_solar_position(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                sun = ephem.Sun(self.observer)
                alt = float(sun.alt) * 180.0 / ephem.pi
                az  = float(sun.az)  * 180.0 / ephem.pi
            self.sun_pos.update({
                "solar_alt": round(alt, 2),
                "solar_az":  round(az, 2),
                "sun_time":  datetime.now().strftime("%m-%d %H:%M:%S"),
            })
        except Exception as e:
            emit_log(f"[SOLAR] Position error: {e}")

    def _sun_path_sunrise_to_sunset(self, interval_minutes=5):
        """Path from next sunrise to next sunset. Fallback to 12h window if needed."""
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                sun = ephem.Sun()
                sunrise_utc = self.observer.next_rising(sun)
                sunset_utc  = self.observer.next_setting(sun)
        except Exception:
            # Fallback: sample next 12h at fixed cadence
            return self._path_next_hours(ephem.Sun, hours=12, interval_minutes=interval_minutes)

        return self._path_between(ephem.Sun, sunrise_utc, sunset_utc, interval_minutes)

    def get_solar_equatorial(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                sun = ephem.Sun(self.observer)
                ra_str = str(sun.ra)
                dec_str = str(sun.dec)
            return {"ra_str": ra_str, "dec_str": dec_str}
        except Exception as e:
            emit_log(f"[SOLAR] RA/DEC error: {e}")
            return {"ra_str": "--:--:--", "dec_str": "--:--:--"}

    # ---------------- Lunar ----------------

    def update_moon_times(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                moon = ephem.Moon()
                moonrise = ephem.localtime(self.observer.next_rising(moon))
                moonset  = ephem.localtime(self.observer.next_setting(moon))
                transit  = ephem.localtime(self.observer.next_transit(moon))
            self.moon_times.update({
                "moonrise": moonrise.strftime("%H:%M"),
                "moonset":  moonset.strftime("%H:%M"),
                "moon_transit": transit.strftime("%H:%M"),
            })
        except Exception as e:
            emit_log(f"[LUNAR] Times error: {e}")

    def update_lunar_position(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                moon = ephem.Moon(self.observer)
                alt = float(moon.alt) * 180.0 / ephem.pi
                az  = float(moon.az)  * 180.0 / ephem.pi
            self.moon_pos.update({
                "lunar_alt": round(alt, 2),
                "lunar_az":  round(az, 2),
                "moon_time": datetime.now().strftime("%m-%d %H:%M:%S"),
            })
        except Exception as e:
            emit_log(f"[LUNAR] Position error: {e}")

    def get_moon_equatorial(self):
        try:
            with self._lock:
                self.observer.date = datetime.utcnow()
                moon = ephem.Moon(self.observer)
                ra_str = str(moon.ra)
                dec_str = str(moon.dec)
            return {"ra_str": ra_str, "dec_str": dec_str}
        except Exception as e:
            emit_log(f"[LUNAR] RA/DEC error: {e}")
            return {"ra_str": "--:--:--", "dec_str": "--:--:--"}

    def get_moon_day_path(self, interval_minutes=5):
        try:
            now = datetime.now()
            today = now.date()
            if solar_cache.get("date_moon") == today and solar_cache.get("path_moon"):
                return solar_cache["path_moon"]

            self.observer.date = now
            moon = ephem.Moon()
            # Robust window: from previous_rising to next_setting if Moon is currently up
            try:
                prev_rise = self.observer.previous_rising(moon)
            except Exception:
                prev_rise = None
            try:
                next_set = self.observer.next_setting(moon)
            except Exception:
                next_set = None

            # Fallback to next_rising→next_setting if previous_rising failed
            if prev_rise and next_set and prev_rise < next_set:
                start_t, end_t = prev_rise, next_set
            else:
                start_t = self.observer.next_rising(moon)
                end_t   = self.observer.next_setting(moon)

            times, t = [], start_t
            while t < end_t:
                times.append(t)
                t = ephem.Date(t + interval_minutes / (24 * 60))

            path = []
            for t in times:
                self.observer.date = t
                m = ephem.Moon(self.observer)
                alt = float(m.alt) * 180.0 / ephem.pi
                az  = float(m.az)  * 180.0 / ephem.pi
                alt = max(0, min(alt, 90))
                az  = az % 360
                timestamp = ephem.localtime(t).strftime("%H:%M")
                path.append({"az": round(az, 2), "alt": round(alt, 2), "time": timestamp})

            solar_cache["date_moon"] = today
            solar_cache["path_moon"] = path
            emit_log(f"[LUNAR] 🌙 Generated {len(path)} moon points")
            return path

        except Exception as e:
            emit_log(f"[LUNAR] Error generating moon path: {e}")
            return []

    # Prefer a robust “next 24h” path for the Moon; its rise/set can be weird.
    def _moon_path_next_24h(self, interval_minutes=5):
        start = ephem.Date(datetime.utcnow())
        end   = ephem.Date(datetime.utcnow() + timedelta(hours=24))
        return self._path_between(ephem.Moon, start, end, interval_minutes)

    # ---------------- Shared path helpers ----------------

    def _path_between(self, body_cls, start_ephem_date, end_ephem_date, interval_minutes):
        path = []
        try:
            t = start_ephem_date
            while t < end_ephem_date:
                with self._lock:
                    self.observer.date = t
                    body = body_cls(self.observer)
                    alt = float(body.alt) * 180.0 / ephem.pi
                    az  = float(body.az)  * 180.0 / ephem.pi
                alt = max(0.0, min(alt, 90.0))
                az  = az % 360.0
                timestamp = ephem.localtime(t).strftime("%H:%M")
                path.append({"az": round(az, 2), "alt": round(alt, 2), "time": timestamp})
                t = ephem.Date(t + interval_minutes / (24 * 60.0))
        except Exception as e:
            emit_log(f"[ASTRO] Path error: {e}")
        return path

    def _path_next_hours(self, body_cls, hours=12, interval_minutes=5):
        start = ephem.Date(datetime.utcnow())
        end   = ephem.Date(datetime.utcnow() + timedelta(hours=hours))
        return self._path_between(body_cls, start, end, interval_minutes)

    # Public path entry point
    def get_full_day_path(self, target="sun", interval_minutes=5):
        target = (target or "sun").lower()
        # cache key includes target and date
        today = datetime.utcnow().date()
        key_path = f"path_{target}"
        key_date = f"date_{target}"
        if solar_cache.get(key_date) == today and solar_cache.get(key_path):
            return solar_cache[key_path]

        if target == "moon":
            path = self._moon_path_next_24h(interval_minutes)
        else:
            path = self._sun_path_sunrise_to_sunset(interval_minutes)

        solar_cache[key_date] = today
        solar_cache[key_path] = path
        emit_log(f"[ASTRO] Generated {len(path)} points for {target}")
        return path

    # ---------------- Unified API ----------------

    def get_data(self):
        """Raw combined snapshot (no mapping)."""
        return {
            **self.sun_times,
            **self.sun_pos,
            **self.moon_times,
            **self.moon_pos,
            "target": self.target_mode,
            "location_profile": self.location_profile,
        }

    def get_equatorial(self, target="sun"):
        """Uniform RA/Dec dict for active target."""
        return self.get_moon_equatorial() if (target or "sun").lower() == "moon" else self.get_solar_equatorial()

    def get_solar_snapshot(self):
        return {
            "alt": self.sun_pos.get("solar_alt"),
            "az":  self.sun_pos.get("solar_az"),
            "rise": self.sun_times.get("sunrise"),
            "set":  self.sun_times.get("sunset"),
            "transit": self.sun_times.get("solar_noon"),
            "time": self.sun_pos.get("sun_time"),
        }

    def get_lunar_snapshot(self):
        return {
            "alt": self.moon_pos.get("lunar_alt"),
            "az":  self.moon_pos.get("lunar_az"),
            "rise": self.moon_times.get("moonrise"),
            "set":  self.moon_times.get("moonset"),
            "transit": self.moon_times.get("moon_transit"),
            "time": self.moon_pos.get("moon_time"),
        }

    def build_frontend_payload(self, target=None):
        """
        Map to the keys your front-end already uses.
        If target == 'moon', we stuff lunar values into the solar_* fields so your existing UI updates.
        """
        tgt = (target or self.target_mode or "sun").lower()
        if tgt == "moon":
            m = self.get_lunar_snapshot()
            payload = {
                "solar_alt":  m["alt"],          # UI already reads these IDs
                "solar_az":   m["az"],
                "sunrise":    m["rise"],
                "solar_noon": m["transit"],
                "sunset":     m["set"],
                "sun_time":   m["time"],

                # also include explicit lunar_* if you add fields later
                "lunar_alt":  m["alt"],
                "lunar_az":   m["az"],
                "moonrise":   m["rise"],
                "moonset":    m["set"],
                "moon_time":  m["time"],

                "target": "moon",
                "location_profile": self.location_profile,
            }
        else:
            s = self.get_solar_snapshot()
            payload = {
                "solar_alt":  s["alt"],
                "solar_az":   s["az"],
                "sunrise":    s["rise"],
                "solar_noon": s["transit"],
                "sunset":     s["set"],
                "sun_time":   s["time"],
                "target": "sun",
                "location_profile": self.location_profile,
            }
        return payload
    
    def clear_path_cache(self):
        for t in ("sun", "moon"):
            solar_cache.pop(f"path_{t}", None)
            solar_cache.pop(f"date_{t}", None)

    # ---------------- Monitor loop ----------------

    def start_monitor(self, socketio, interval=20):
        def loop():
            emit_log("[ASTRO] Monitor loop running")
            # initial push
            self.update_sun_times()
            self.update_moon_times()
            self.update_solar_position()
            self.update_lunar_position()
            socketio.emit("astro_update", self.build_frontend_payload())

            count = 0
            while True:
                socketio.sleep(interval)
                self.update_solar_position()
                self.update_lunar_position()

                # refresh rise/set a few times/day
                if interval > 0 and (count % max(1, (6*60*60)//interval) == 0):
                    self.update_sun_times()
                    self.update_moon_times()

                socketio.emit("astro_update", self.build_frontend_payload())
                count += 1

        socketio.start_background_task(loop)