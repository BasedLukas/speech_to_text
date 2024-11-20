import time
import threading
from PIL import Image, ImageDraw
from pystray import Icon

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
    not_recording_icon = create_icon("gray")

    icon = Icon("RecordingIndicator", not_recording_icon, "Not Recording")

    def icon_runner():
        icon.run()

    # Start the icon thread
    icon_thread = threading.Thread(target=icon_runner, daemon=True)
    icon_thread.start()

    return icon