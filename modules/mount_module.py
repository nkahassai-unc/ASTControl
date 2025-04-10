# Mount Module
# Description: This module communicates between the Flask app and the Indigo server.

# Central controller for telescope mount actions

import threading
import time
from utilities import network_utils, config

# === Public API ===

def slew(direction: str, rate: str = None) -> bool:
    """Send mount slewing command in cardinal direction."""
    if direction.upper() not in ("N", "S", "E", "W"):
        return False
    if rate:
        set_rate(rate)

    cmd = f'indigo_prop_tool "{MOUNT_DEVICE}" MOUNT_MOTION.{_axis(direction)}=ON'
    res = _ssh(cmd)
    return res["returncode"] == 0

def stop_mount() -> bool:
    """Stop all mount motion."""
    cmd = f'indigo_prop_tool "{MOUNT_DEVICE}" MOUNT_ABORT=ON'
    return _ssh(cmd)["returncode"] == 0

def set_rate(rate: str) -> bool:
    """Set slewing rate: solar / slow / fast."""
    if rate not in ("solar", "slow", "fast"):
        return False

    # Map user rate to INDIGO rate values if needed
    # This example assumes symbolic values
    cmd = f'indigo_prop_tool "{MOUNT_DEVICE}" MOUNT_TRACK_RATE.TRACKING_RATE_{rate.upper()}=ON'
    res = _ssh(cmd)
    if res["returncode"] == 0:
        state["slew_rate"] = rate
        _update()
        return True
    return False

def get_state() -> dict:
    """Return current mount state."""
    return state


# === Polling Loop ===

_poll_thread = None
_running = False

def start_monitor(interval=5):
    """Start polling mount coordinates via INDIGO."""
    global _poll_thread, _running
    if _poll_thread and _poll_thread.is_alive():
        return
    _running = True
    _poll_thread = threading.Thread(target=_poll_loop, args=(interval,), daemon=True)
    _poll_thread.start()

def stop_monitor():
    """Stop background polling."""
    global _running
    _running = False


# === Internal Functions ===

def _poll_loop(interval):
    """Poll current RA/DEC from the mount device."""
    while _running:
        try:
            ra_res = _ssh(f'indigo_prop_tool "{MOUNT_DEVICE}" MOUNT_EQUATORIAL_RA')
            dec_res = _ssh(f'indigo_prop_tool "{MOUNT_DEVICE}" MOUNT_EQUATORIAL_DEC')

            if ra_res["stdout"]:
                state["ra"] = _parse_val(ra_res["stdout"])

            if dec_res["stdout"]:
                state["dec"] = _parse_val(dec_res["stdout"])

            _update()

        except Exception as e:
            print(f"[Mount Monitor Error] {e}")

        time.sleep(interval)

def _parse_val(output: str) -> str:
    """Extract value from indigo_prop_tool output line."""
    for line in output.splitlines():
        if "value=" in line:
            return line.split("value=")[-1].strip()
    return "--"

def _axis(dir: str) -> str:
    """Translate cardinal direction to INDIGO axis."""
    return "0" if dir.upper() in ("W", "E") else "1"

def _ssh(cmd: str) -> dict:
    """Run SSH command on Pi."""
    client = network_utils.get_ssh_client(
        config.RASPBERRY_PI_IP,
        config.SSH_USERNAME,
        config.SSH_PASSWORD
    )
    return network_utils.run_ssh_command(client, cmd)

def _update():
    state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
