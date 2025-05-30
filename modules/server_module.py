# Server Module
# Remote INDIGO server controller for Flask GUI or CLI

from utilities.network_utils import (
    get_ssh_client,
    stream_ssh_output,
    run_ssh_command,
    check_remote_port
)
import threading

class IndigoServer:
    def __init__(self, ip, username, password, port=7624):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.running = False
        self.thread = None

    def connect(self):
        if not self.client:
            self.client = get_ssh_client(self.ip, self.username, self.password)

    def start(self, callback):
        """Start INDIGO server remotely and stream output via callback."""
        self.connect()
        self.running = True

        def runner():
            try:
                # Kill existing instances to avoid bind error
                run_ssh_command(self.client, "pkill -f indigo_server")
                stream_ssh_output(self.client, "indigo_server", callback)
            except Exception as e:
                callback(f"[ERROR] INDIGO server stream failed: {e}")
            self.running = False

        self.thread = threading.Thread(target=runner, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop INDIGO server process remotely."""
        self.connect()
        self.running = False
        return run_ssh_command(self.client, "pkill -f indigo_server")

    def check_status(self):
        """Check if INDIGO server is active on port 7624."""
        return check_remote_port(self.ip, self.port)

    def get_status(self):
        """Return current status as a simple dict."""
        return {
            "running": self.check_status()
        }