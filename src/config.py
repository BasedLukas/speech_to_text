# 'tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 'large-v3-turbo', 'turbo'
MODEL_NAME = 'base.en' 
AUDIO_DEVICE = 'default' #  ; Name of the audio device or 'default'
COMBINATIONS = [
    ["ctrl", "f1"],   # Left Ctrl + F1
    ["ctrl_r", "f1"]  # Right Ctrl + F1
]
DEVICE_NAME = None # Specify the audio input device by name
SAMPLERATE = 16000  # Whisper uses 16000 Hz
CHANNELS = 1
LOG_LEVEL = "INFO" # INFO or DEBUG
