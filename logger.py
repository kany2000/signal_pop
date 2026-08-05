import logging
import os
from config import LOG_LEVEL, LOG_FILE

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

logger = logging.getLogger("signal_pop")


# Custom exception classes
class SignalPopError(Exception):
    """Base exception class for Signal Pop errors."""

    pass


class NewsParseError(SignalPopError):
    """Raised when there's an error parsing news content."""

    pass


class ImageGenerationError(SignalPopError):
    """Raised when there's an error generating images."""

    pass


class TTSGenerationError(SignalPopError):
    """Raised when there's an error generating TTS audio."""

    pass


class VideoBuildError(SignalPopError):
    """Raised when there's an error building the video."""

    pass


# Helper function for logging and raising custom exceptions
def log_and_raise(exception_class, message, *args, **kwargs):
    logger.error(message, *args, **kwargs)
    raise exception_class(message)


# Example usage:
# try:
#     # some operation that might fail
# except SomeError as e:
#     log_and_raise(SignalPopError, f"Error in operation: {e}")
