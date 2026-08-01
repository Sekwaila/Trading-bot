"""
SEKWAILA OMEGA X
Logging configuration
"""

import logging
from logging import StreamHandler, Formatter

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = StreamHandler()
        handler.setFormatter(Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        # Prevent duplicate logs if root logger already configured elsewhere
        logger.propagate = False
    return logger
