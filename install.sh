#!/bin/bash

# Define paths 
CWD=$(pwd)
VENV_PATH="$CWD/venv"  # Path to the virtual environment
SOURCE_SERVICE="$CWD/src/whisper.service"
TARGET_SERVICE="$HOME/.config/systemd/user/whisper.service"


# Ensure the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH. Please create it before installing."
    exit 1
fi
# Run tests to ensure everything is setup correctly
echo "Running environment tests..."
if ! "$VENV_PATH/bin/python" -c "from src.test import test_all; exit(0 if test_all() else 1)"; then
    echo "Environment tests failed. Fix the issues before installing."
    exit 1
fi


# Create the systemd user directory if it doesn't exist
mkdir -p "$HOME/.config/systemd/user"

# Remove any existing file or symlink at the target location
if [ -e "$TARGET_SERVICE" ] || [ -L "$TARGET_SERVICE" ]; then
    rm -f "$TARGET_SERVICE"
fi
# Modify the service file to include the correct CWD and copy it to the systemd directory
sed "s|%CWD%|$CWD|g" "$SOURCE_SERVICE" > "$TARGET_SERVICE"

# start everythin
systemctl --user daemon-reload
systemctl --user enable whisper.service
systemctl --user restart whisper.service


echo "Service installed and enabled. Use 'journalctl --user -u whisper.service -f' to view logs"
