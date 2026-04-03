"""Logging configuration for the trading bot.

Provides a file-only logger that writes to trading_bot.log.
No output is sent to stdout or stderr.
"""
import logging
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_bot.log")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Track which loggers have already been configured to avoid duplicate handlers
_configured_loggers: set = set()


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that writes exclusively to trading_bot.log.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured Logger instance with FileHandler only.
    """
    logger = logging.getLogger(name)

    if name not in _configured_loggers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_FILE)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        # Prevent propagation to root logger (which may have StreamHandlers)
        logger.propagate = False
        _configured_loggers.add(name)

    return logger
