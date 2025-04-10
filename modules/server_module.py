# Server Module
# Description: Remote INDIGO server controller for Flask GUI or CLI

from utilities.network_utils import get_ssh_client, stream_ssh_output, run_ssh_command
import threading

class IndigoServer:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.client = None
        self.running = False

    def connect(self):
        if not self.client:
            self.client = get_ssh_client(self.ip, self.username, self.password)

    def start(self, callback):
        """Start INDIGO server remotely and stream output via callback."""
        self.connect()
        self.running = True

        def runner():
            stream_ssh_output(self.client, "indigo_server", callback)
            self.running = False

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()

    def stop(self):
        """Stop INDIGO server process remotely."""
        self.connect()
        return run_ssh_command(self.client, "pkill -f indigo_server")
