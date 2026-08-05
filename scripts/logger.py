"""
Bridge module: loads logger from project root by file path.
Avoids circular import by using importlib.util instead of `from logger import`.
"""
import importlib.util
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_logger = os.path.join(_PROJECT_ROOT, "logger.py")

_spec = importlib.util.spec_from_file_location("_root_logger", _root_logger)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_root_logger"] = _mod
_spec.loader.exec_module(_mod)

logger = _mod.logger
log_and_raise = _mod.log_and_raise
SignalPopError = _mod.SignalPopError
NewsParseError = _mod.NewsParseError
ImageGenerationError = _mod.ImageGenerationError
TTSGenerationError = _mod.TTSGenerationError
VideoBuildError = _mod.VideoBuildError

__all__ = [
    "logger",
    "log_and_raise",
    "SignalPopError",
    "NewsParseError",
    "ImageGenerationError",
    "TTSGenerationError",
    "VideoBuildError",
]
