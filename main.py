import sys


from src.test import test_whisper, test_requirements
from src import logger
from src.main import WhisperService


if __name__ == "__main__":
    if not test_requirements or not test_whisper():
        sys.exit(1)
    try:
        whisper_service = WhisperService()
        whisper_service.start()
    except KeyboardInterrupt:
        logger.info("Service terminated by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


    