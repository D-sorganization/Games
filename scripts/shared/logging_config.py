"""Shared logging configuration for scripts."""

import logging


def setup_script_logging(
    level: int = logging.INFO,
    format_string: str = "%(levelname)s: %(message)s",
) -> logging.Logger:
    """
    Configure logging for scripts with consistent formatting.

    Args:
        level: The logging level to use
        format_string: The format string for log messages

    Returns:
        A logger instance for the calling module
    """
    logging.basicConfig(level=level, format=format_string)
    return logging.getLogger(__name__)


def setup_detailed_logging(
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure logging with detailed formatting including timestamps.

    Args:
        level: The logging level to use

    Returns:
        A logger instance for the calling module
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)
