import paramiko
import threading

class IndigoServerController:
    def __init__(self, ip, username="pi", password="your_password", log_callback=None):
        """
        Initialize the SSH connection details.
        :param ip: IP address of the Raspberry Pi.
        :param username: SSH username (default is 'pi').
        :param password: SSH password.
        :param log_callback: Function to handle log messages.
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.log_callback = log_callback
        self.ssh_client = None
        self.running = False

    def connect(self):
        """Establish an SSH connection to the Raspberry Pi."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(hostname=self.ip, username=self.username, password=self.password)
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"SSH connection failed: {e}")
            return False

    def disconnect(self):
        """Close the SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()

    def log(self, message):
        """Log messages using the provided callback."""
        if self.log_callback:
            self.log_callback(message)

    def start_indigo_server(self):
        """Start the INDIGO server via SSH and stream logs."""
        if not self.ssh_client:
            if not self.connect():
                return "Failed to connect to the Raspberry Pi."
        try:
            self.running = True
            self.log("Starting INDIGO server...")
            stdin, stdout, stderr = self.ssh_client.exec_command("indigo_server")

            # Stream logs in a separate thread
            def stream_logs(stream):
                for line in iter(stream.readline, ""):
                    if not self.running:
                        break
                    self.log(line.strip())

            threading.Thread(target=stream_logs, args=(stdout,), daemon=True).start()
            threading.Thread(target=stream_logs, args=(stderr,), daemon=True).start()
            return "INDIGO server started."
        except Exception as e:
            return f"Failed to start INDIGO server: {e}"

    def kill_indigo_server(self):
        """Kill the INDIGO server via SSH."""
        if not self.ssh_client:
            if not self.connect():
                return "Failed to connect to the Raspberry Pi."
        try:
            self.running = False
            stdin, stdout, stderr = self.ssh_client.exec_command("sudo pkill -f indigo_server")
            self.log("INDIGO server stopped.")
            return stdout.read().decode()
        except Exception as e:
            return f"Failed to kill INDIGO server: {e}"