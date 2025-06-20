# Indigo JSON Client
# Connects to INDIGO server using JSON protocol over TCP.

import socket
import threading
import json
import time

class IndigoJSONClient:
    def __init__(self, host='indigosky.local', reconnect_interval=5):
        self.host = host
        self.port = 7624
        self.sock = None
        self.listener_thread = None
        self.callbacks = {}  # action_type -> function(msg)
        self.connected = False
        self.lock = threading.Lock()  # for send() thread safety
        self.reconnect_interval = reconnect_interval
        self.retry_count = 0
        self.stop_flag = threading.Event()

    def connect(self, max_retries=10):
        while not self.stop_flag.is_set() and self.retry_count < max_retries:
            try:
                print(f"[INDIGO] Connecting to {self.host}:{self.port}... (Attempt {self.retry_count + 1})")
                self.sock = socket.create_connection((self.host, self.port), timeout=10)
                self.connected = True
                print("[INDIGO] Connected.")
                self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.listener_thread.start()
                return
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                print(f"[INDIGO] Connection failed: {e}. Retrying in {self.reconnect_interval}s...")
                time.sleep(self.reconnect_interval)
                self.retry_count += 1

        print(f"[INDIGO] Failed to connect after {max_retries} attempts.")
        self.connected = False

    def send(self, message: dict, quiet: bool = False):
        """Send a JSON message to INDIGO."""
        if not self.connected:
            if not quiet:
                print("[INDIGO] Not connected — skipping send.")
            return
        raw = json.dumps(message) + '\n'
        with self.lock:
            try:
                self.sock.sendall(raw.encode())
            except (BrokenPipeError, OSError) as e:
                if not quiet:
                    print(f"[INDIGO] Send failed: {e}")
                self.connected = False
                if not quiet:
                    raise

    def _listen_loop(self):
        """Continuously read and dispatch JSON messages from the INDIGO server."""
        buffer = ''
        try:
            while not self.stop_flag.is_set():
                data = self.sock.recv(4096).decode()
                if not data:
                    print("[INDIGO] Connection closed by remote.")
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self._dispatch(line.strip())
        except (ConnectionResetError, socket.timeout, OSError) as e:
            print(f"[INDIGO] Listener error: {e}")
        finally:
            self.connected = False
            self.sock.close()
            print("[INDIGO] Disconnected. Attempting to reconnect...")
            print("[INDIGO] Reconnection skipped after listener exit.")

    def _dispatch(self, line: str):
        """Handle a single JSON message from INDIGO."""
        try:
            msg = json.loads(line)
            kind = msg.get("action") or msg.get("name")
            if kind in self.callbacks:
                self.callbacks[kind](msg)
            else:
                print(f"[INDIGO] Unhandled message: {msg}")
        except json.JSONDecodeError:
            print("[INDIGO] Failed to parse:", line)

    def on(self, kind, callback):
        """Register callback for message kind ('set', 'get', etc)."""
        self.callbacks[kind] = callback

    def close(self):
        """Clean shutdown."""
        self.stop_flag.set()
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("[INDIGO] Client closed.")
