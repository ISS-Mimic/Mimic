# Pi/utils/logger.py
"""
Central logging for the Mimic GUI.
Usage in any module / screen:
    from utils.logger import log_info, log_error        # quick helpers
    # …or…
    from utils.logger import log                        # full Logger object
"""

from __future__ import annotations

import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from os import environ

# ---------------------------------------------------------------------------
# Log-file destination  (~/Mimic/Pi/Logs/mimic.log)
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parents[1]          # …/Mimic/Pi
_LOG_DIR  = _BASE_DIR / "Logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "mimic.log"

# ---------------------------------------------------------------------------
# Root-logger configuration  (execute once)
# ---------------------------------------------------------------------------
def _configure_root() -> logging.Logger:
    root = logging.getLogger("Mimic")        # single app-wide logger
    if root.handlers:                        # already configured
        return root

    # Get log level from environment variable, default to ERROR
    log_level_str = environ.get('MIMIC_LOG_LEVEL', 'ERROR').upper()
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = log_level_map.get(log_level_str, logging.ERROR)
    
    root.setLevel(log_level)

    # rotating file handler --------------------------------------------------
    fh = RotatingFileHandler(_LOG_FILE, maxBytes=1_048_576, backupCount=5)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    fmt.converter = time.gmtime                 # UTC timestamps (optional)
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)                 # File handler always captures all levels
    root.addHandler(fh)

    # console handler (INFO+) ------------------------------------------------
    # Enable console output only if MIMIC_CONSOLE_LOGGING is set
    if environ.get('MIMIC_CONSOLE_LOGGING', '').lower() in ('1', 'true', 'yes', 'on'):
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            "%(levelname)s: [%(filename)s:%(lineno)d] %(message)s"))
        ch.setLevel(log_level)                 # Console handler respects the configured level
        root.addHandler(ch)
        print(f"Console logging enabled at {log_level_str} level")
    # ch = logging.StreamHandler()
    # ch.setFormatter(logging.Formatter(
    #     "%(levelname)s: [%(filename)s:%(lineno)d] %(message)s"))
    # ch.setLevel(logging.INFO)                  # change to WARNING for prod
    # root.addHandler(ch)

    return root


log = _configure_root()            # initialise immediately

# ---------------------------------------------------------------------------
# Convenience wrappers keep caller’s stack-frame (Python 3.8+)
# ---------------------------------------------------------------------------
def log_info(msg: str, *a, **kw) -> None:
    log.info(msg, *a, stacklevel=2, **kw)

def log_warning(msg: str, *a, **kw) -> None:
    log.warning(msg, *a, stacklevel=2, **kw)

def log_error(msg: str, *a, **kw) -> None:
    log.error(msg, *a, stacklevel=2, **kw)
