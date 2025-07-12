# Solar Module
# Solar position module using PyEphem 
# Set for latitude and longitude of Chapel Hill, NC

import ephem
from datetime import datetime, timezone, timedelta

class SolarPosition:
    def __init__(self, latitude=35.9132, longitude=-79.0558):
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.observer = ephem.Observer()
        self.observer.lat = self.latitude
        self.observer.lon = self.longitude
        self.observer.elev = 0
        self.local_tz = timezone(timedelta(hours=-5))  # Adjust for your time zone

        self.sun_times = {
            "sunrise": "--",
            "sunset": "--",
            "solar_noon": "--"
        }

        self.solar_position = {
            "solar_alt": "--",
            "solar_az": "--",
            "sun_time": "--"
        }

        self.update_sun_times()

    def update_sun_times(self):
        try:
            self.observer.date = datetime.utcnow()
            sunrise = ephem.localtime(self.observer.next_rising(ephem.Sun()))
            sunset = ephem.localtime(self.observer.next_setting(ephem.Sun()))
            transit = ephem.localtime(self.observer.next_transit(ephem.Sun()))

            self.sun_times.update({
                "sunrise": sunrise.strftime("%H:%M"),
                "sunset": sunset.strftime("%H:%M"),
                "solar_noon": transit.strftime("%H:%M")
            })
        except Exception as e:
            print(f"[Solar] Error fetching sun times: {e}")

    def update_solar_position(self):
        try:
            self.observer.date = datetime.utcnow()
            sun = ephem.Sun(self.observer)
            alt = float(sun.alt) * 180.0 / ephem.pi
            az = float(sun.az) * 180.0 / ephem.pi

            self.solar_position.update({
                "solar_alt": round(alt, 2) if alt > 0 else "Below",
                "solar_az": round(az, 2),
                "sun_time": datetime.now().strftime("%m-%d %H:%M:%S")
            })
        except Exception as e:
            print(f"[Solar] Error calculating solar position: {e}")

    def get_solar_equatorial(self):
        try:
            self.observer.date = datetime.utcnow()
            sun = ephem.Sun(self.observer)
            ra = sun.ra  # in radians internally, but str is formatted
            dec = sun.dec
            return {
                "ra_solar": str(ra),   # HH:MM:SS
                "dec_solar": str(dec)  # ±DD:MM:SS
            }
        except Exception as e:
            print(f"[Solar] Error getting RA/DEC: {e}")
            return {
                "ra_solar": "--:--:--",
                "dec_solar": "--:--:--"
            }
        
    def get_data(self):
        return {**self.sun_times, **self.solar_position}

    def start_monitor(self, socketio, interval=20):
        def loop():
            self.update_sun_times()
            self.update_solar_position()
            socketio.emit("solar_update", self.get_data())

            count = 0
            while True:
                socketio.sleep(interval)
                self.update_solar_position()

                if count % (6 * 60 * 60 // interval) == 0:
                    self.update_sun_times()

                socketio.emit("solar_update", self.get_data())
                count += 1

        socketio.start_background_task(loop)