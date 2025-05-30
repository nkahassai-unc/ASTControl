# Mount Module
# Interface logic controlling mount via INDIGO + SSH

import threading
import time
from utilities.network_utils import get_ssh_client, run_ssh_command_with_log, run_ssh_command

_socketio = None

def set_socketio(instance):
    global _socketio
    _socketio = instance

class MountController:
    def __init__(self, ip, username, password, use_simulator=True):
        self.ip = ip
        self.username = username
        self.password = password
        self.client = None
        self.device = "Mount Agent"
        self.use_simulator = use_simulator
        self.running = True
        self.connect()
        self.attach_mount()
        self.log_properties()
        self._start_coord_monitor()

    def connect(self):
        if not self.client:
            self.client = get_ssh_client(self.ip, self.username, self.password)

    def emit_status(self, state):
        _socketio.emit("mount_status", state)

    def run_indigo_prop_command(self, cli_args, callback):
        self.connect()
        full_cmd = f"indigo_prop_tool {cli_args}"
        callback(f"[MOUNT_MODULE] $ {full_cmd}")
        run_ssh_command_with_log(self.client, full_cmd, callback)

    def attach_mount(self):
        cmd = "indigo_prop_tool set 'Mount Agent.AGENT_ATTACH.MOUNT=Mount Simulator'"
        run_ssh_command_with_log(self.client, cmd, lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))

    def log_properties(self):
        cmd = "indigo_prop_tool list 'Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES'"
        run_ssh_command_with_log(self.client, cmd, lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))

    def _start_coord_monitor(self):
        def loop():
            while self.running:
                coords = self.get_coordinates()
                _socketio.emit("mount_coordinates", coords)
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()

    def get_coordinates(self):
        ra_cmd = 'indigo_prop_tool get "Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.RA"'
        dec_cmd = 'indigo_prop_tool get "Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.DEC"'

        ra = "--"
        dec = "--"

        try:
            ra_out = run_ssh_command(self.client, ra_cmd)
            dec_out = run_ssh_command(self.client, dec_cmd)

            for line in ra_out["stdout"].splitlines():
                if "=" in line:
                    ra = line.split("=")[1].strip()

            for line in dec_out["stdout"].splitlines():
                if "=" in line:
                    dec = line.split("=")[1].strip()

        except Exception as e:
            print(f"[MountModule] get_coordinates error: {e}")

        return {"ra": ra, "dec": dec}

    def slew(self, direction, rate="solar"):
        self.connect()
        self.emit_status(f"Slewing {direction.upper()} at {rate.upper()}")

        prop_map = {
            "north": "Mount Agent.MOUNT_MOTION_DEC.NORTH",
            "south": "Mount Agent.MOUNT_MOTION_DEC.SOUTH",
            "east":  "Mount Agent.MOUNT_MOTION_RA.EAST",
            "west":  "Mount Agent.MOUNT_MOTION_RA.WEST"
        }

        speed_map = {
            "solar": "Mount Agent.MOUNT_TRACK_RATE.SOLAR",
            "slow":  "Mount Agent.MOUNT_SLEW_RATE.CENTERING",
            "fast":  "Mount Agent.MOUNT_SLEW_RATE.MAX"
        }

        rate_cmd = f"-p '{speed_map.get(rate.lower())}=On'"
        dir_cmd  = f"-p '{prop_map.get(direction.lower())}=On'"

        run_ssh_command_with_log(self.client, f"{rate_cmd} {dir_cmd}", lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))

    def stop(self):
        self.connect()
        self.emit_status("Manual Stop")
        cmd = (
            "-p 'Mount Agent.MOUNT_MOTION_DEC.NORTH=Off' "
            "-p 'Mount Agent.MOUNT_MOTION_DEC.SOUTH=Off' "
            "-p 'Mount Agent.MOUNT_MOTION_RA.EAST=Off' "
            "-p 'Mount Agent.MOUNT_MOTION_RA.WEST=Off'"
        )
        run_ssh_command_with_log(self.client, cmd, lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))

    def track_sun(self):
        self.connect()
        self.emit_status("Tracking Sun")
        cmd = (
            "-p 'Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.RA=12.0' "
            "-p 'Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.DEC=45.0' "
            "-p 'Mount Agent.AGENT_START_PROCESS.SLEW=On'"
        )
        run_ssh_command_with_log(self.client, cmd, lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))

    def park(self):
        self.connect()
        self.emit_status("Slewing to Park")
        cmd = (
            "-p 'Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.RA=0.0' "
            "-p 'Mount Agent.AGENT_MOUNT_EQUATORIAL_COORDINATES.DEC=90.0' "
            "-p 'Mount Agent.AGENT_START_PROCESS.SLEW=On'"
        )
        run_ssh_command_with_log(self.client, cmd, lambda msg: _socketio.emit("server_log", f"[MOUNT_MODULE] {msg}"))