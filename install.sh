#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to print messages
print_message() {
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# Get the absolute path of the current directory (repository directory)
REPO_DIR="$(pwd)"
VENV_DIR="$REPO_DIR/venv"
SERVICE_FILE_TEMPLATE="$REPO_DIR/whisper.service"
SERVICE_FILE_TEMP="$REPO_DIR/whisper.service.tmp"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SYSTEMD_SERVICE_PATH="$SYSTEMD_USER_DIR/whisper.service"
ENV_FILE="$REPO_DIR/whisper.env"

print_message "Starting Whisper Transcription Service Installation..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python3 and try again."
    exit 1
fi

# Detect DISPLAY and XAUTHORITY
if [ -z "$DISPLAY" ]; then
    echo "DISPLAY environment variable is not set. Please ensure you are running this script within a graphical session."
    exit 1
fi

if [ -z "$XAUTHORITY" ]; then
    # Attempt to find XAUTHORITY
    XAUTHORITY_PATH="/run/user/$(id -u)/gdm/Xauthority"
    if [ -f "$XAUTHORITY_PATH" ]; then
        XAUTHORITY="$XAUTHORITY_PATH"
    else
        # Fallback to default Xauthority in home directory
        XAUTHORITY="$HOME/.Xauthority"
        if [ ! -f "$XAUTHORITY" ]; then
            echo "Could not determine XAUTHORITY. Please set it manually."
            exit 1
        fi
    fi
fi

print_message "Detected Environment Variables:"
echo "DISPLAY=$DISPLAY"
echo "XAUTHORITY=$XAUTHORITY"

# Create Python virtual environment
if [ ! -d "$VENV_DIR" ]; then
    print_message "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_message "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_message "Installing dependencies..."
pip install -r "$REPO_DIR/requirements.txt"

# Deactivate the virtual environment
deactivate

# Create the Environment File with DISPLAY and XAUTHORITY
print_message "Creating environment file..."
echo "DISPLAY=$DISPLAY" > "$ENV_FILE"
echo "XAUTHORITY=$XAUTHORITY" >> "$ENV_FILE"

# Prepare the systemd service file by replacing placeholders with actual paths
print_message "Configuring systemd service file..."

# Get the absolute path to the Python executable and main.py
PYTHON_EXEC="$VENV_DIR/bin/python"
MAIN_PY="$REPO_DIR/main.py"

# Replace placeholders in the service file template
sed \
    -e "s|%EXEC_START%|$PYTHON_EXEC $MAIN_PY|g" \
    -e "s|%WORKING_DIR%|$REPO_DIR|g" \
    -e "s|%ENV_FILE%|$ENV_FILE|g" \
    "$SERVICE_FILE_TEMPLATE" > "$SERVICE_FILE_TEMP"

# Ensure the systemd user directory exists
mkdir -p "$SYSTEMD_USER_DIR"

# Copy the configured service file to the systemd user directory
cp "$SERVICE_FILE_TEMP" "$SYSTEMD_SERVICE_PATH"

# Clean up temporary service file
rm "$SERVICE_FILE_TEMP"

# Reload systemd user daemon to recognize the new service
print_message "Reloading systemd user daemon..."
systemctl --user daemon-reload

# Enable the service to start on login
print_message "Enabling whisper.service..."
systemctl --user enable whisper.service

# Start the service
print_message "Starting whisper.service..."
systemctl --user start whisper.service

print_message "Whisper Transcription Service installed and started successfully."

echo "To view logs, run: journalctl --user -u whisper.service -f"
echo "To stop the service, run: systemctl --user stop whisper.service"
