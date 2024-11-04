import logging
import json


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for logging.
    Formats log records as JSON objects.
    """

    def format(self, record):
        """
        Format the specified record as a JSON object.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The JSON formatted log record.
        """
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
        }
        return json.dumps(log_record)


def get_service_logger(name: str):
    """
    Get a configured logger with a JSON formatter.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger.
    """
    # Set up the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create and set the JSON formatter
    json_formatter = JSONFormatter()
    console_handler.setFormatter(json_formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    return logger
