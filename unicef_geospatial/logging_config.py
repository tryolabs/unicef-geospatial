import logging
from contextvars import ContextVar
from logging import Filter
from typing import Any, Literal

# Create a context variable to store logger context without a default
logger_context: ContextVar[dict[str, Any]] = ContextVar("logger_context")


class ContextFilter(Filter):
    """Logging filter to add `ContextVar` contents to log records as attributes."""

    def filter(self, record: logging.LogRecord) -> Literal[True]:
        """Add context variable contents to log record.

        Args:
            record (logging.LogRecord): Log record being augmented.

        Returns:
            Literal[True]: Never filter the record as this filter only augments it.
        """
        context = logger_context.get({})
        for key, value in context.items():
            setattr(record, key, value)
        return True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger with a given name and level.

    Args:
        name (str): Logger name. Forwarded to `logging.getLogger`.
        level (int, optional): Level for the returned logger. Defaults to `logging.INFO`.

    Returns:
        logging.Logger: Configured logger with a `StreamHandler` (for console logging with a
            standardized format) and a `ContextFilter` to add context variable contents to all log
            records.
    """
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.setLevel(level)

        context_filter = ContextFilter()
        logger.addFilter(context_filter)

        logger.setLevel(logging.INFO)

    return logger
