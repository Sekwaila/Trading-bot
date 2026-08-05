"""
SEKWAILA OMEGA X – Logging Utility
Features:
- Console + rotating file output
- Logs stored in logs/omega.log (auto‑created directory)
- UTF‑8 encoding for emojis and non‑ASCII
- Configurable log level (from config.py)
- Detailed timestamps (YYYY‑MM‑DD HH:MM:SS)
- Rotating files: 5 MB max, 5 backups
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Try to import config for LOG_LEVEL, fallback to INFO
try:
    from config import LOG_LEVEL
except ImportError:
    LOG_LEVEL = "INFO"

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "omega.log"

# Map string level to logging constant
LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOG_LEVEL_INT = LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with console and rotating file handlers.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL_INT)
    logger.propagate = False

    # ---- Formatter (with full timestamp) ----
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- Console Handler ----
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(LOG_LEVEL_INT)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ---- Rotating File Handler ----
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(LOG_LEVEL_INT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
