"""
Logging utility for the application
Provides file-based logging with proper formatting and configuration
"""
import os
import datetime
import logging
from pathlib import Path

# Configure logging
def setup_logger(name="teshi"):
    """
    Setup a logger with file output
    Args:
        name (str): Logger name
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create logs directory if it doesn't exist
    logs_dir = Path.home() / ".teshi" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_file = logs_dir / f"teshi_{timestamp}.log"

    # Create file handler
    file_handler = logging.FileHandler(
        log_file,
        mode='a',  # Append mode
        encoding='utf-8'
    )

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add formatter to handler
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    return logger

def log_message(logger, message, level="INFO"):
    """
    Log a message with the specified level
    Args:
        logger: Logger instance
        message (str): Message to log
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_levels = {
        'DEBUG': lambda: logger.debug(message),
        'INFO': lambda: logger.info(message),
        'WARNING': lambda: logger.warning(message),
        'ERROR': lambda: logger.error(message),
        'CRITICAL': lambda: logger.critical(message)
    }

    if level in log_levels:
        log_levels[level]()
    else:
        logger.info(message)  # Default to INFO if invalid level

# Global logger instance
_logger = setup_logger()

def get_logger():
    """
    Get the global logger instance
    Returns:
        logging.Logger: Global logger instance
    """
    return _logger