import threading
import sys
from typing import List, Optional, Tuple, Dict, Any

import sounddevice as sd
import numpy as np
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode

from src.test import test_all
from src.utils import (
    create_icon, 
    get_tray_icon, 
    check_combination,
    get_device_index
)
from src import logger
from src.config import (
    SAMPLERATE, 
    CHANNELS, 
    COMBINATIONS, 
    MODEL_NAME,
)


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
    logger.debug(f"Audio Volume: {volume_norm:.4f}")


def transcribe_and_insert(audio: List[np.ndarray]) -> None:
    global audio_data
    logger.info("Starting transcription...")
    try:
        audio = np.concatenate(audio, axis=0)
        audio = np.squeeze(audio)
        result = model.transcribe(audio)
        text = result["text"].strip()
        logger.info(f"\"{text}\"")
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
    except Exception as e:
        logger.error(f"Error inserting text: {e}")


def on_press(key: keyboard.Key) -> None:
    global is_recording, stream, audio_data
    current_keys.add(key)  # Add key to current_keys

    # Check if any combination is fully pressed
    if check_combination(current_keys, COMBINATIONS):
        if not is_recording:
            with lock:
                is_recording = True
                audio_data = []
                logger.info("Recording started.")
                tray_icon.icon = create_icon("red")  # Update tray icon to red
                tray_icon.title = "Recording"  # Update tray title
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
    if not check_combination(current_keys, COMBINATIONS):
        if is_recording:
            with lock:
                is_recording = False
                tray_icon.icon = create_icon("green")  # Update tray icon to green
                tray_icon.title = "Not Recording"  # Update tray title
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
    if not test_all():
        sys.exit(1)
    try:
        current_keys: set[keyboard.Key] = set()
        is_recording: bool = False
        audio_data: List[np.ndarray] = []
        stream: Optional[sd.InputStream] = None
        lock = threading.Lock()
        keyboard_controller = Controller()
        tray_icon = get_tray_icon() 
        INPUT_DEVICE_INDEX = get_device_index()
        logger.info("Loading whisper model. This may take time to download...")
        model = whisper.load_model(MODEL_NAME)
        logger.info("Whisper model loaded successfully.")
        start_listener()
    except KeyboardInterrupt:
        logger.info("Service terminated by user.")
        tray_icon.stop()  # Stop the tray icon on exit
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        tray_icon.stop()  # Stop the tray icon on exit
        sys.exit(1)