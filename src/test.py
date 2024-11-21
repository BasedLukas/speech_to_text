import importlib
import warnings
from . import logger
from .config import MODEL_NAME

def test_whisper():
    try:
        import whisper
    except Exception as e:
        logger.error(f"Could not import whisper: {e}")
        return False
    try:
        warnings.filterwarnings("ignore", category=FutureWarning) 
        model = whisper.load_model(MODEL_NAME)
    except Exception as e:
        logger.error(f"Couldn't load model: {e}")
        return False
    return True
    
def test_requirements():
    imports = [
        "sounddevice", 
        "PIL" ,
        "pystray",
        "numpy" ,
        "whisper",
        "pynput",
    ]
    try:
        for package_name in imports:
            importlib.import_module(package_name)
    except Exception as e:
        logger.error(f"Not all requirements satisfied: {e}")
        return False    
    return True

def test_all():
    return test_whisper() and test_requirements()