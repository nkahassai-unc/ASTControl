# Startup script to run FireCapture.

import subprocess

subprocess.run(["./run_fc.sh"], check=True)

print("Running FireCapture...")
print("FireCapture completed successfully!")