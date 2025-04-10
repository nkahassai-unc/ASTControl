# Arduino Module
# Description: Central Arduino controller for UI interaction

import threading
import time
from utilities import network_utils, config

# === Arduino State (from config) ===
state = config.ARDUINO_STATE

# === Public UI API ===

def set_dome(state_cmd: str) -> bool:
    """Set dome state: 'open' or 'close'."""
    if state_cmd not in ("open", "close"):
        return False
    res = _send(f"DOME_{state_cmd.upper()}")
    if _ok(res):
        state["dome"] = state_cmd.upper()
        _update()
        return True
    return False

def set_etalon(index: int, value: int) -> bool:
    """Set etalon1 or etalon2 to specific position (0–180)."""
    if index not in (1, 2) or not (0 <= value <= 180):
        return False
    res = _send(f"ETALON{index}_SET:{value}")
    if _ok(res):
        state[f"etalon{index}"] = value
        _update()
        return True
    return False

def get_state() -> dict:
    """Full Arduino state for UI display."""
    return state

def get_dome() -> str:
    return state.get("dome", "UNKNOWN")

def get_etalon(index: int) -> int:
    return state.get(f"etalon{index}", 90)


# === Background Polling Thread ===

_poll_thread = None
_running = False

def start_monitor(interval=5):
    """Start Arduino state polling."""
    global _poll_thread, _running
    if _poll_thread and _poll_thread.is_alive():
        return
    _running = True
    _poll_thread = threading.Thread(target=_poll_loop, args=(interval,), daemon=True)
    _poll_thread.start()

def stop_monitor():
    """Stop polling loop."""
    global _running
    _running = False


# === Internals ===

def _poll_loop(interval):
    """Loop to refresh dome + etalon state."""
    while _running:
        try:
            dome = _send("DOME_STATUS")["stdout"].strip()
            if dome in ("OPEN", "CLOSED"):
                state["dome"] = dome

            for i in (1, 2):
                raw = _send(f"ETALON{i}_GET")["stdout"].strip()
                if raw.isdigit():
                    state[f"etalon{i}"] = int(raw)

            _update()

        except Exception as e:
            print(f"[Arduino Monitor Error] {e}")
        time.sleep(interval)

def _send(cmd: str) -> dict:
    """Send a command to Arduino via serial-over-SSH."""
    return network_utils.run_python_serial_command(_client(), cmd)

def _ok(result: dict) -> bool:
    return result.get("stdout", "").strip().upper() == "OK"

def _client():
    """Get reusable SSH client."""
    return network_utils.get_ssh_client(
        config.RASPBERRY_PI_IP,
        config.SSH_USERNAME,
        config.SSH_PASSWORD
    )

def _update():
    """Update the last_updated timestamp."""
    state["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
