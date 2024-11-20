#!/bin/bash


# Define paths for the service file
CWD=$(pwd)
SOURCE_SERVICE="$CWD/src/whisper.service"
TARGET_SERVICE="$HOME/.config/systemd/user/whisper.service"

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
systemctl --user start whisper.service


echo "Service installed and enabled. Use journalctl --user -u whisper.service -f to view logs"
