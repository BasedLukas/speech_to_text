import sounddevice as sd
import numpy as np
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode
import threading
import pyperclip
import time
import sys
import logging

### CONFIGS ###
# Hotkey combination: Ctrl + F1
COMBINATION = {keyboard.Key.ctrl, keyboard.Key.f1}
DEVICE_NAME = None # Specify the audio input device by name
SAMPLERATE = 16000  # Whisper uses 16000 Hz
CHANNELS = 1
LOG_LEVEL = logging.INFO

### OBJECTS ###
current_keys = set()
is_recording = False
audio_data = []
stream = None
lock = threading.Lock()
keyboard_controller = Controller()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("whisper.service")


def list_input_devices():
    """List all available input devices."""
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    if not input_devices:
        logger.error("No input devices found.")
        sys.exit(1)
    logger.info("Available input devices:")
    for idx, device in enumerate(input_devices):
        logger.info(f"{idx}: {device['name']}")
    return input_devices


def get_default_input_device():
    """Get the default input device index."""
    default_device = sd.default.device
    if isinstance(default_device, tuple):
        default_input = default_device[0]
    else:
        # If default_device is a single integer
        default_input = default_device
    if default_input is None:
        # Fallback to first available input device
        input_devices = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
        if not input_devices:
            raise ValueError("No input devices available.")
        default_input = input_devices[0]['index']
    return default_input


def get_device_index():
    """Determine the input device index to use."""
    if DEVICE_NAME:
        devices = sd.query_devices()
        for device in devices:
            if DEVICE_NAME.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                logger.info(f"Selected audio input device '{device['name']}' with index {device['index']}.")
                return device['index']
        logger.warning(f"Device '{DEVICE_NAME}' not found. Falling back to default input device.")
    
    # Use default input device
    try:
        default_input = get_default_input_device()
        default_device_info = sd.query_devices(default_input, 'input')
        logger.info(f"Using default audio input device '{default_device_info['name']}' with index {default_input}.")
        return default_input
    except Exception as e:
        logger.error(f"Error getting default input device: {e}")
        sys.exit(1)


def audio_callback(indata, frames, time_info, status):
    global audio_data
    if status:
        logger.error(f"Recording error: {status}")
    audio_data.append(indata.copy())
    
    # Log audio data statistics
    volume_norm = np.linalg.norm(indata) * 10
    logger.debug(f"Audio Volume: {volume_norm}")


def transcribe_and_insert(audio):
    global audio_data
    logger.info("Starting transcription...")
    try:
        # Convert audio to the format Whisper expects
        audio = np.concatenate(audio, axis=0)
        audio = np.squeeze(audio)

        # Transcribe using Whisper
        result = model.transcribe(audio)
        text = result["text"].strip()

        logger.info(f"Transcription result: {text}")

        if text:
            # Insert the transcribed text at the cursor location
            insert_text(text)
        else:
            logger.info("No speech detected during transcription.")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")


def insert_text(text):
    try:
        # Copy text to clipboard
        pyperclip.copy(text)
        time.sleep(0.1)  # Small delay to ensure clipboard is updated

        # Simulate Ctrl + V to paste
        with keyboard_controller.pressed(Key.ctrl):
            keyboard_controller.press('v')
            keyboard_controller.release('v')

        logger.info("Transcribed text inserted successfully.")
        # notify("Whisper Service: Text inserted.")
    except Exception as e:
        logger.error(f"Error inserting text: {e}")


def on_press(key):
    global is_recording, stream, audio_data
    if key in COMBINATION:
        current_keys.add(key)
        if all(k in current_keys for k in COMBINATION):
            if not is_recording:
                with lock:
                    is_recording = True
                    audio_data = []
                    logger.info("Recording started.")
                    try:
                        # Start the audio stream with specified device
                        stream = sd.InputStream(
                            samplerate=SAMPLERATE,
                            channels=CHANNELS,
                            callback=audio_callback,
                            device=INPUT_DEVICE_INDEX
                        )
                        stream.start()
                        logger.info("Audio stream started.")
                    except Exception as e:
                        logger.error(f"Error starting audio stream: {e}")
                        is_recording = False


def on_release(key):
    global is_recording, stream
    if key in COMBINATION:
        current_keys.discard(key)
        if is_recording:
            with lock:
                is_recording = False
                try:
                    # Stop the audio stream
                    stream.stop()
                    stream.close()
                    logger.info("Recording stopped.")
                    # notify("Whisper Service: Recording stopped.")

                    # Transcribe in a separate thread
                    threading.Thread(target=transcribe_and_insert, args=(audio_data.copy(),)).start()
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")
                    # notify("Whisper Service: Failed to stop recording.")


def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        logger.info("Whisper service is now listening for Ctrl + F1...")
        listener.join()


if __name__ == "__main__":

    # init audio device
    try:
        INPUT_DEVICE_INDEX = get_device_index()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    # Initialize the Whisper model
    try:
        model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        sys.exit(1)
    # listen
    try:
        start_listener()
    except KeyboardInterrupt:
        logger.info("Service terminated by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
