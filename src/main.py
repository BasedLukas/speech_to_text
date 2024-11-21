import threading
from typing import List, Optional, Tuple, Dict, Any

import sounddevice as sd
import numpy as np
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode
from PIL import Image, ImageDraw
from pystray import Icon
from pynput.keyboard import Key, KeyCode


from . import logger
from .config import (
    SAMPLERATE, 
    CHANNELS, 
    COMBINATIONS,
    DEVICE_NAME,
    MODEL_NAME,
    TIMER_DURATION,
)


class WhisperService:
    def __init__(self):
        # Configurations
        self.samplerate = SAMPLERATE
        self.channels = CHANNELS
        self.combinations = COMBINATIONS
        self.device_name = DEVICE_NAME
        self.model_name = MODEL_NAME
        self.timer_duration = TIMER_DURATION
        self.audio_data = []
        
        # State
        self.model = None
        self.is_recording = False
        self.currently_depressed = set()
        self.lock = threading.Lock()
        self.usage_timer = None
        
        # Components
        self.tray_icon = self.get_tray_icon()
        self.keyboard_controller = Controller()
        self.stream = None

        logger.info(f"WhisperService().__init__() success")

    ### ICON MANAGEMENT ###
    
    def create_icon(self, color: str) -> Image.Image:
        size = 64
        image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, size - 8, size - 8), fill=color)
        return image

    def get_tray_icon(self) -> "Icon":
        recording_icon = self.create_icon("red")
        not_recording_icon = self.create_icon("green")
        standby_icon = self.create_icon("grey")

        icon = Icon("RecordingIndicator", not_recording_icon, "Not Recording")

        def icon_runner():
            icon.run()

        icon_thread = threading.Thread(target=icon_runner, daemon=True)
        icon_thread.start()

        return icon

    def update_tray_icon(self, color: str, title: str) -> None:
        self.tray_icon.icon = self.create_icon(color)
        self.tray_icon.title = title

    ### AUDIO DEVICE ###
    
    def get_device_index(self) -> int:
        if self.device_name:
            devices = sd.query_devices()
            for device in devices:
                if self.device_name.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                    return device['index']
        return sd.default.device[0]  # Default input device index

    ### AUDIO HANDLING ###

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.error(f"Recording error: {status}")    
        # Append audio data and log shape
        self.audio_data.append(indata.copy())
        logger.debug(f"Audio callback received data shape: {indata.shape}, dtype: {indata.dtype}")


    ### MODEL MANAGEMENT ###

    def load_model(self):
        try:
            self.model = whisper.load_model(self.model_name)  # Assign model to self.model
            logger.info("Whisper model loaded successfully.")
            self.update_tray_icon("green", "Ready")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.model = None

    def unload_model(self):
        with self.lock:
            self.model = None
            self.update_tray_icon("grey", "Dormant")
            logger.info("Model unloaded due to inactivity.")

    def reset_timer(self):
        with self.lock:
            if self.usage_timer:
                self.usage_timer.cancel()
            self.usage_timer = threading.Timer(self.timer_duration, self.unload_model)
            self.usage_timer.start()

    ### TRANSCRIPTION ###

    def transcribe_and_insert(self):
        try:
            logger.debug("transcribe called")
            
            if not self.model:
                logger.info("Loading model...")
                self.load_model()
            
            if not self.audio_data:
                logger.warning("No audio data available for transcription.")
                return
            
            self.reset_timer()
            # Combine and validate audio data
            audio = np.concatenate(self.audio_data, axis=0)
            self.audio_data.clear()  # Clear audio data after combining
            
            if audio.shape[0] == 0:
                logger.error("Audio data is empty after concatenation.")
                return
            
            # Ensure audio is mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Convert to float32 if necessary
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Limit audio length to 60 seconds
            max_length = self.samplerate * 60  # 60 seconds at self.samplerate
            if len(audio) > max_length:
                logger.warning(f"Audio length exceeds 30 seconds. Truncating...")
                audio = audio[:max_length]
            
            logger.debug(f"Audio data after preprocessing: shape {audio.shape}, dtype {audio.dtype}")
            
            # Transcribe using Whisper model
            logger.info("Starting transcription...")
            result = self.model.transcribe(audio, fp16=False)  # Ensure FP16 is disabled if using CPU
            text = result.get("text", "").strip()
            
            if text:
                logger.info(f"'{text}'")
                for char in text:
                    self.keyboard_controller.type(char)
            else:
                logger.info("No transcription result detected.")
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")


    ### KEYBOARD LISTENER ###

    def parse_key(self, key_str):
        if hasattr(Key, key_str):
            return getattr(Key, key_str)
        return KeyCode.from_char(key_str)

    def check_combination(self):
        try:
            for combo in self.combinations:
                parsed_combo = {self.parse_key(k) for k in combo}
                if parsed_combo.issubset(self.currently_depressed):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error in check_combination: {e}")
            return False


    def on_press(self, key):
        try:
            self.currently_depressed.add(key)
            
            # Check if a combination is active
            if self.check_combination() and not self.is_recording:
                logger.debug(f"Key pressed: {key}, currently_depressed: {self.currently_depressed}")
                with self.lock:
                    self.is_recording = True
                    self.audio_data = []  # Clear previous audio data
                    logger.info("Recording started.")
                    self.update_tray_icon("red", "Recording")
                    
                    # Start audio stream
                    self.stream = sd.InputStream(
                        samplerate=self.samplerate,
                        channels=self.channels,
                        callback=self.audio_callback,
                        device=self.get_device_index()
                    )
                    self.stream.start()
                    logger.info("Audio stream started.")
        except Exception as e:
            logger.error(f"Error in on_press: {e}")

    def on_release(self, key):
        try:
            self.currently_depressed.discard(key)
            
            # Stop recording if the combination is no longer active
            if not self.check_combination() and self.is_recording:
                logger.debug(f"Key released: {key}, currently_depressed: {self.currently_depressed}")
                with self.lock:
                    self.is_recording = False
                    self.update_tray_icon("green", "Not Recording")
                    
                    # Stop and close the stream
                    if self.stream:
                        self.stream.stop()
                        self.stream.close()
                        self.stream = None
                        logger.info("Recording stopped.")
                    
                    threading.Thread(target=self.transcribe_and_insert).start()
        except Exception as e:
            logger.error(f"Error in on_release: {e}")

    ### MAIN LOGIC ###

    def start(self):
        try:
            logger.info("Loading Whisper Model...")
            self.load_model()  # Load model at the start
            logger.info(f"Listening for any of {COMBINATIONS}")
            listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            listener.start()
            listener.join()
        except Exception as e:
            logger.error(f"Error during service start: {e}")


