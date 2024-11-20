import sounddevice as sd
import numpy as np
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode

import threading
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any

from config import DEVICE_NAME, SAMPLERATE, CHANNELS, COMBINATIONS, LOG_LEVEL


def list_input_devices() -> List[Dict[str, Any]]:
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
    try:
        default_input = get_default_input_device()
        default_device_info = sd.query_devices(default_input, 'input')
        logger.info(f"Using default audio input device '{default_device_info['name']}' with index {default_input}.")
        return default_input
    except Exception as e:
        logger.error(f"Error getting default input device: {e}")
        sys.exit(1)


def audio_callback(
    indata: np.ndarray,
    frames: int,
    time_info: Dict[str, float],
    status: sd.CallbackFlags
) -> None:
    """
    Callback function for audio input.

    Args:
        indata (np.ndarray): The input audio data.
        frames (int): The number of audio frames.
        time_info (Dict[str, float]): Timing information.
        status (sd.CallbackFlags): Status of the callback.
    """
    global audio_data
    if status:
        logger.error(f"Recording error: {status}")
    audio_data.append(indata.copy())
    volume_norm = np.linalg.norm(indata) * 10
    logger.debug(f"Audio Volume: {volume_norm}")


def transcribe_and_insert(audio: List[np.ndarray]) -> None:
    global audio_data
    logger.info("Starting transcription...")
    try:
        audio = np.concatenate(audio, axis=0)
        audio = np.squeeze(audio)
        result = model.transcribe(audio)
        text = result["text"].strip()
        logger.info(f"Transcription result: {text}")
        if text:
            insert_text(text)
        else:
            logger.info("No speech detected during transcription.")
    except Exception as e:
        logger.error(f"Error during transcription: {e}")


def insert_text(text: str) -> None:
    try:
        for char in text:
            keyboard_controller.type(char)
        logger.info("Transcribed text inserted successfully.")
    except Exception as e:
        logger.error(f"Error inserting text: {e}")


def on_press(key: keyboard.Key) -> None:
    global is_recording, stream, audio_data
    current_keys.add(key)  # Add key to current_keys
    # Check if any combination is fully pressed
    if any(combo.issubset(current_keys) for combo in COMBINATIONS):  
        if not is_recording:
            with lock:
                is_recording = True
                audio_data = []
                logger.info("Recording started.")
                try:
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


def on_release(key: keyboard.Key) -> None:
    global is_recording, stream
    current_keys.discard(key)  # Remove key from current_keys
    # Check if all keys in any combination have been released
    if not any(combo.issubset(current_keys) for combo in COMBINATIONS):  
        if is_recording:
            with lock:
                is_recording = False
                try:
                    stream.stop()
                    stream.close()
                    logger.info("Recording stopped.")
                    threading.Thread(target=transcribe_and_insert, args=(audio_data.copy(),)).start()
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")


def start_listener() -> None:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        logger.info("Whisper service is now listening for Ctrl + F1 or Ctrl_r + F1...")
        listener.join()


if __name__ == "__main__":
    current_keys: set[keyboard.Key] = set()
    is_recording: bool = False
    audio_data: List[np.ndarray] = []
    stream: Optional[sd.InputStream] = None
    lock = threading.Lock()
    keyboard_controller = Controller()
    logging.basicConfig(
        level=LOG_LEVEL,
        format="[%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("whisper.service")

    try:
        INPUT_DEVICE_INDEX = get_device_index()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    try:
        model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        sys.exit(1)

    try:
        start_listener()
    except KeyboardInterrupt:
        logger.info("Service terminated by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)