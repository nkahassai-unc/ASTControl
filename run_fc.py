# Startup script to run FireCapture.

import subprocess

# Ensure the run_fc.sh script has execute permissions (755)
subprocess.run(["chmod", "755", "./run_fc.sh"], check=True)

# Run the FireCapture script
print("Running FireCapture...")
subprocess.run(["./run_fc.sh"], check=True)

# Print message to indicate that FireCapture has started successfully
print("FireCapture started successfully!")