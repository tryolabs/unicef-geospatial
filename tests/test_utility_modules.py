"""
Unit tests for utility modules including logging, document processing, and app configuration.
"""

from unicef_geospatial.logging_config import get_logger


class TestLoggingConfig:
    """Test cases for logging configuration module."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_logger")

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")

    def test_get_logger_with_different_names(self):
        """Test that get_logger returns different loggers for different names."""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")

        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_get_logger_same_name_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("same_logger")
        logger2 = get_logger("same_logger")

        assert logger1 is logger2

    def test_setup_logging_with_different_levels(self):
        """Test setup_logging with different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in levels:
            get_logger("test_logger", level)

    def test_logger_methods_work(self):
        """Test that logger methods work correctly."""
        logger = get_logger("test_methods")

        logger.info("Test info message")
        logger.error("Test error message")
        logger.warning("Test warning message")
        logger.debug("Test debug message")
