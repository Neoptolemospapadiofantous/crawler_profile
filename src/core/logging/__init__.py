"""
Logging configuration module.
Provides structured logging with JSON and text formats.
"""
import os
import sys
import logging
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import structlog
from structlog.stdlib import LoggerFactory

from config.settings import get_settings

# Module-level logger storage
_loggers: Dict[str, logging.Logger] = {}
_logger_manager: Optional['LoggerManager'] = None


class LoggerManager:
    """Manages application-wide logging configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize logger manager.
        
        Args:
            config_path: Path to logging configuration file
        """
        self.settings = get_settings()
        self.config_path = config_path or Path("config/logging.yaml")
        self._initialized = False
        
    def initialize(self):
        """Initialize logging configuration."""
        if self._initialized:
            return
            
        # Create log directory
        self.settings.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        if self.config_path.exists():
            self._load_yaml_config()
        else:
            self._load_default_config()
            
        # Configure structlog
        self._configure_structlog()
        
        self._initialized = True
        
    def _load_yaml_config(self):
        """Load logging configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Update log file paths
            for handler in config.get('handlers', {}).values():
                if 'filename' in handler:
                    file_path = Path(handler['filename'])
                    if not file_path.is_absolute():
                        try:
                            file_path = file_path.relative_to(self.settings.log_dir)
                        except ValueError:
                            pass
                        handler['filename'] = str(self.settings.log_dir / file_path)
                    else:
                        handler['filename'] = str(file_path)
                    
            logging.config.dictConfig(config)
        except Exception as e:
            print(f"Failed to load logging config: {e}", file=sys.stderr)
            self._load_default_config()
            
    def _load_default_config(self):
        """Load default logging configuration."""
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'json': {
                    'format': '%(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.settings.log_level,
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': self.settings.log_level,
                    'formatter': 'json' if self.settings.log_format == 'json' else 'standard',
                    'filename': str(self.settings.log_dir / 'app.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'root': {
                'level': self.settings.log_level,
                'handlers': ['console', 'file']
            }
        }
        
        logging.config.dictConfig(config)
        
    def _configure_structlog(self):
        """Configure structlog for structured logging."""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        if self.settings.log_format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
            
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        if not self._initialized:
            self.initialize()
            
        if name not in _loggers:
            _loggers[name] = structlog.get_logger(name)
            
        return _loggers[name]


def get_logger_manager() -> LoggerManager:
    """Get the global logger manager instance."""
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
        _logger_manager.initialize()
        
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    manager = get_logger_manager()
    return manager.get_logger(name)


def get_main_logger() -> logging.Logger:
    """Get the main application logger."""
    return get_logger("main")


# Initialize logging on import
get_logger_manager()

__all__ = [
    'LoggerManager',
    'get_logger_manager',
    'get_logger',
    'get_main_logger',
]                                                                               