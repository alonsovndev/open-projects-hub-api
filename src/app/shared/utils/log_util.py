import os
import logging

# Log Format and Timestamp Format
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Returns a logger instance configured to output logs to the console,
    compatible with Datadog log ingestion.
    :param name: The name of the logger (defaults to the module name).
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # Prevent duplicate handlers in case of repeated calls
        return logger

    # Set the log level (default to INFO, can be overridden via an environment variable)
    log_level = LOG_LEVEL
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # Add the console handler to the logger
    logger.addHandler(console_handler)

    return logger


log = get_logger(__name__)
