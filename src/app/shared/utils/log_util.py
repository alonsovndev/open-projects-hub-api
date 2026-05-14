import os
import logging
from pythonjsonlogger.json import JsonFormatter

# Log Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT_JSON = os.getenv("LOG_FORMAT_JSON", "true").lower() == "true"

# Plain text format (legacy)
PLAIN_TEXT_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CustomJsonFormatter(JsonFormatter):
    """
    Custom JSON formatter that includes standard fields for observability.
    
    Automatically includes:
    - timestamp (ISO format)
    - level (INFO, ERROR, etc.)
    - message
    - logger name
    - any extra fields passed via extra={...} in log calls
    """
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to the log record."""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Include module and function for debugging
        if record.pathname:
            log_record['module'] = record.module
        if record.funcName:
            log_record['function'] = record.funcName


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Returns a logger instance configured for structured logging.
    
    Supports both JSON (default) and plain-text formats via LOG_FORMAT_JSON env var.
    
    JSON format includes:
    - timestamp: Unix timestamp
    - level: Log level (INFO, ERROR, etc.)
    - message: Log message
    - logger: Logger name
    - Additional context fields via extra={...}
    
    Args:
        name: Logger name (defaults to module name)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:  # Prevent duplicate handlers
        return logger

    log_level = LOG_LEVEL
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Choose formatter based on configuration
    if LOG_FORMAT_JSON:
        # JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        # Plain text formatter (legacy)
        formatter = logging.Formatter(PLAIN_TEXT_FORMAT, datefmt=DATE_FORMAT)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


log = get_logger(__name__)
