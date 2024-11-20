from pynput import keyboard

model_name = 'base'  # Whisper model to use (e.g., base, small, medium, large)
audio_device = 'default' #  ; Name of the audio device or 'default'
COMBINATIONS = [
    {keyboard.Key.ctrl, keyboard.Key.f1},  # Left Ctrl + F1
    {keyboard.Key.ctrl_r, keyboard.Key.f1}  # Right Ctrl + F1
]
DEVICE_NAME = None # Specify the audio input device by name
SAMPLERATE = 16000  # Whisper uses 16000 Hz
CHANNELS = 1
LOG_LEVEL = "INFO" # or DEBUG