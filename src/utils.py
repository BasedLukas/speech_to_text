import time
import threading
from PIL import Image, ImageDraw
from pystray import Icon
from pynput.keyboard import Key, KeyCode
from typing import List, Optional, Tuple, Dict, Any
import sounddevice as sd

from src import logger
from src.config import *

def check_combination(current_keys, combinations):
    """
    Check if any combination of keys is fully pressed.

    Args:
        current_keys (set): A set of currently pressed keys.
        combinations (list): A list of key combinations as lists of strings.

    Returns:
        bool: True if a combination is pressed, False otherwise.
    """
    def parse_key(key_str):
        # Convert string to Key or KeyCode
        if hasattr(Key, key_str):
            return getattr(Key, key_str)  # Convert to special Key
        return KeyCode.from_char(key_str)  # Convert to KeyCode for characters

    for combo in combinations:
        parsed_combo = {parse_key(k) for k in combo}
        if parsed_combo.issubset(current_keys):
            return True
    return False


def create_icon(color: str) -> Image.Image:
    """Create a circular icon with the given color."""
    size = 64
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, size - 8, size - 8), fill=color)
    return image


def get_tray_icon():
    """Create and return a tray icon instance."""
    recording_icon = create_icon("red")
    not_recording_icon = create_icon("blue")

    icon = Icon("RecordingIndicator", not_recording_icon, "Not Recording")

    def icon_runner():
        icon.run()

    # Start the icon thread
    icon_thread = threading.Thread(target=icon_runner, daemon=True)
    icon_thread.start()

    return icon


def list_input_devices() -> List[Dict[str, Any]]:
    """List all available input devices."""
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    return input_devices


def get_default_input_device() -> int:
    """Get the default input device index."""
    default_device = sd.default.device
    default_input = default_device[0] if isinstance(default_device, tuple) else default_device
    if default_input is None:
        input_devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
        if not input_devices:
            raise ValueError("No input devices available.")
        default_input = input_devices[0]['index']
    return default_input


def get_device_index() -> int:
    """Determine the input device index to use."""
    if DEVICE_NAME:
        devices = sd.query_devices()
        for device in devices:
            if DEVICE_NAME.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                logger.info(f"Selected audio input device '{device['name']}' with index {device['index']}.")
                return device['index']
        logger.warning(f"Device '{DEVICE_NAME}' not found. Falling back to default input device.")
    default_input = get_default_input_device()
    default_device_info = sd.query_devices(default_input, 'input')
    logger.info(f"Using default audio input device '{default_device_info['name']}' with index {default_input}.")
    return default_input

