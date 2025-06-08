"""
Centralized logging configuration and management.
"""

import logging
import logging.config
import yaml
from pathlib import Path
from typing import Optional
import structlog
from config.settings import get_settings


class LoggerManager:
    """Centralized logger management for the application."""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def initialize(cls, config_path: Optional[Path] = None) -> None:
        """Initialize the logging system."""
        if cls._initialized:
            return
        
        settings = get_settings()
        
        # Ensure log directory exists
        settings.logging.dir.mkdir(parents=True, exist_ok=True)
        
        # Load logging configuration
        if config_path is None:
            config_path = Path("config/logging.yaml")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        else:
            # Fallback to basic configuration
            cls._setup_basic_logging()
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        cls._initialized = True
    
    @classmethod
    def _setup_basic_logging(cls) -> None:
        """Setup basic logging configuration as fallback."""
        settings = get_settings()
        
        logging.basicConfig(
            level=getattr(logging, settings.logging.level),
            format=settings.logging.format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(settings.logging.dir / "app.log")
            ]
        )
    
    @classmethod
    def get_logger(cls, name: str) -> structlog.stdlib.BoundLogger:
        """Get a logger instance with the given name."""
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            # Create a structured logger
            logger = structlog.get_logger(f"profile_automation.{name}")
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def get_standard_logger(cls, name: str) -> logging.Logger:
        """Get a standard Python logger instance."""
        if not cls._initialized:
            cls.initialize()
        
        return logging.getLogger(f"profile_automation.{name}")


# Convenience functions for common loggers
def get_profile_logger() -> structlog.stdlib.BoundLogger:
    """Get the profiles logger."""
    return LoggerManager.get_logger("profiles")


def get_database_logger() -> structlog.stdlib.BoundLogger:
    """Get the database logger."""
    return LoggerManager.get_logger("database")


def get_task_logger() -> structlog.stdlib.BoundLogger:
    """Get the tasks logger."""
    return LoggerManager.get_logger("tasks")


def get_automation_logger() -> structlog.stdlib.BoundLogger:
    """Get the automation logger."""
    return LoggerManager.get_logger("automation")


def get_main_logger() -> structlog.stdlib.BoundLogger:
    """Get the main application logger."""
    return LoggerManager.get_logger("main")


# Initialize logging on import
LoggerManager.initialize()