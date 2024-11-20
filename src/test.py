import importlib
from . import logger
from .config import MODEL_NAME

def test_whisper():
    try:
        import whisper
    except Exception as e:
        logger.error(f"Could not import whisper: {e}")
        return False
    try: 
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
        "src.utils",
    ]
    try:
        for package_name in imports:
            importlib.import_module(package_name)
    except Exception as e:
        logger.error(f"Not all requirements satisfied: {e}")
        return False    
    return True

def test_utils():
    try:
        from src import utils
        assert len(utils.list_input_devices()) >  0
        utils.get_default_input_device()
        utils.get_device_index()
    except Exception as e:
        logger.error(f"{e}")
        return False
    return True

def test_all()->bool:
    return test_requirements() and test_whisper() and test_utils()
