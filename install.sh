#!/bin/bash

# Get the current working directory
CWD=$(pwd)

# Define paths for the service file
SOURCE_SERVICE="$CWD/whisper.service"
TARGET_SERVICE="$HOME/.config/systemd/user/whisper.service"

# Create the systemd user directory if it doesn't exist
mkdir -p "$HOME/.config/systemd/user"

# Remove any existing file or symlink at the target location
if [ -e "$TARGET_SERVICE" ] || [ -L "$TARGET_SERVICE" ]; then
    rm -f "$TARGET_SERVICE"
fi

# Modify the service file to include the correct CWD and copy it to the systemd directory
sed "s|%CWD%|$CWD|g" "$SOURCE_SERVICE" > "$TARGET_SERVICE"

# Reload systemd to recognize the updated service
systemctl --user daemon-reload

# Enable the service
systemctl --user enable whisper.service

echo "Service installed and enabled. Use 'systemctl --user start whisper.service' to start the service."
