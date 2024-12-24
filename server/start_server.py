import subprocess
import time

class StartServer:
    def __init__(self, output_callback):
        """Initialize with the output callback function."""
        self.output_callback = output_callback
        self.process = None

    def log(self, message):
        """Log output through the callback to app.py"""
        self.output_callback(message)

    def start_indigo_server(self):
        """Start the INDIGO server and monitor its output."""
        try:
            self.log("Starting INDIGO server...")
            self.process = subprocess.Popen(
                ["indigo_server"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Capture stdout and stderr in real-time
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log(line.strip())

            for line in iter(self.process.stderr.readline, ''):
                if line:
                    self.log(f"ERROR: {line.strip()}")

        except Exception as e:
            self.log(f"Error starting INDIGO server: {str(e)}")

        finally:
            if self.process and self.process.poll() is not None:
                self.log("INDIGO server process stopped unexpectedly.")
                self.process = None

    def run(self):
        """Run the server starter continuously, restarting if it crashes."""
        while True:
            self.start_indigo_server()
            time.sleep(10)  # Wait before attempting to restart if the server crashes

def main(output_callback):
    """Main function for running the server starter."""
    server_starter = StartServer(output_callback)
    server_starter.run()

# Standalone testing
if __name__ == "__main__":
    def output_callback(log_message):
        print(log_message)  # Print to terminal for testing
    main(output_callback)
