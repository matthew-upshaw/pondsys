# pondsys.utils.logging_config.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import logging

from pondsys.utils.styler import TextStyler

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

class CustomFormatter(logging.Formatter):
    """
    Custom formatter for logging messages.
    """
    custom_format = "%(levelname)s: %(message)s"

    FORMATS = {
        logging.DEBUG: TextStyler.WHITE + custom_format + TextStyler.RESET,
        logging.INFO: TextStyler.WHITE + custom_format + TextStyler.RESET,
        logging.WARNING: TextStyler.YELLOW + custom_format + TextStyler.RESET,
        logging.ERROR: TextStyler.RED + custom_format + TextStyler.RESET,
        logging.CRITICAL: TextStyler.RED + TextStyler.BOLD + custom_format + TextStyler.RESET,
    }

    def format(self, record):
        """
        Format the log record.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
def setup_logger():
    """
    Setup logging configuration.
    """
    logger = logging.getLogger("pondsys")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    formatter = CustomFormatter()
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger

logger = setup_logger()