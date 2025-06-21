#!/usr/bin/env python3
"""
Logging Manager for Slack Claude Code Integration

Manages logging configuration, file handlers, and log formatting
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggingManager:
    """
    Manages logging configuration for the Slack Claude Code integration

    Responsibilities:
    - Set up file and console logging handlers
    - Configure log formatters
    - Manage log files and directories
    - Provide logger instances
    """

    def __init__(self, logger_name: str = "slack_claude_monitor") -> None:
        """
        Initialize logging manager

        Args:
            logger_name: Name for the logger
        """
        self.logger_name = logger_name
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup detailed logging with file output"""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Configure logger
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # File handler for detailed logs
        log_file = logs_dir / f"slack_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler for basic info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Detailed formatter for file
        format_str = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
        file_formatter = logging.Formatter(format_str)
        file_handler.setFormatter(file_formatter)

        # Simple formatter for console
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info(f"Logging initialized. Log file: {log_file}")
        return logger

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance

        Args:
            name: Logger name (if None, returns the main logger)

        Returns:
            Logger instance
        """
        if name is None:
            return self.logger

        # Create child logger
        child_logger = self.logger.getChild(name)
        return child_logger

    def log_info(self, message: str) -> None:
        """Log an info message"""
        self.logger.info(message)

    def log_debug(self, message: str) -> None:
        """Log a debug message"""
        self.logger.debug(message)

    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """Log an error message"""
        self.logger.error(message)

    def log_critical(self, message: str) -> None:
        """Log a critical message"""
        self.logger.critical(message)

    def get_current_log_file(self) -> Path:
        """
        Get the current log file path

        Returns:
            Path to current log file
        """
        return Path("logs") / f"slack_monitor_{datetime.now().strftime('%Y%m%d')}.log"

    def log_error_with_traceback(self, message: str, traceback: str) -> None:
        """
        Log an error message with traceback

        Args:
            message: Error message
            traceback: Traceback string
        """
        self.logger.error(message)
        self.logger.error(f"Full traceback:\n{traceback}")

    def log_initialization_info(self, claude_user_id: str, channels_count: int) -> None:
        """
        Log initialization information

        Args:
            claude_user_id: Claude user ID
            channels_count: Number of configured channels
        """
        self.logger.info("Initialized SlackSocketMonitor")
        self.logger.info(f"Claude User ID: {claude_user_id}")
        self.logger.info(f"Loaded configurations for {channels_count} channels")
