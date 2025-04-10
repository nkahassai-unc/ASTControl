# network_utils.py
# Low-level SSH and serial command execution for remote devices

import paramiko

def get_ssh_client(ip, username, password):
    """Establish and return an active SSH connection to the remote device."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=username, password=password)
    return client

def run_ssh_command(client, command):
    """Run a one-off command using an active SSH client."""
    stdin, stdout, stderr = client.exec_command(command)
    return {
        "stdout": stdout.read().decode().strip(),
        "stderr": stderr.read().decode().strip(),
        "returncode": stdout.channel.recv_exit_status()
    }

def stream_ssh_output(client, command, callback):
    """Stream stdout and stderr line-by-line from a remote process via SSH."""
    channel = client.get_transport().open_session()
    channel.exec_command(command)

    while True:
        if channel.recv_ready():
            output = channel.recv(1024).decode().strip()
            if output:
                callback(output)
        if channel.recv_stderr_ready():
            error = channel.recv_stderr(1024).decode().strip()
            if error:
                callback(f"ERR: {error}")
        if channel.exit_status_ready():
            break

def run_python_serial_command(client, serial_command, port="/dev/ttyACM0"):
    """Send a command to Arduino over serial via remote Python script."""
    escaped = serial_command.replace('"', '\\"')
    py = (
        f'import serial; '
        f's=serial.Serial("{port}",9600,timeout=2); '
        f's.write(b"{escaped}\\n"); '
        f'print(s.readline().decode().strip()); '
        f's.close()'
    )
    return run_ssh_command(client, f'python3 -c "{py}"')
