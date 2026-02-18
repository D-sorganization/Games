"""Shared logging configuration for scripts."""

import logging


def setup_script_logging(
    name: str = __name__,
    level: int = logging.INFO,
    format_string: str = "%(levelname)s: %(message)s",
) -> logging.Logger:
    """
    Configure logging for scripts with consistent formatting.

    Args:
        name: Logger name (typically ``__name__`` from the caller).
        level: The logging level to use.
        format_string: The format string for log messages.

    Returns:
        A logger instance for the calling module.
    """
    logging.basicConfig(level=level, format=format_string)
    return logging.getLogger(name)
