"""
Application configuration settings using Pydantic for type safety and validation.
"""

from typing import Optional, List
from pathlib import Path
from pydantic import BaseSettings, Field, validator
from pydantic.networks import AnyHttpUrl
import os


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=3306, env="DB_PORT")
    name: str = Field(default="profile_automation", env="DB_NAME")
    user: str = Field(env="DB_USER")
    password: str = Field(env="DB_PASSWORD")
    url: Optional[str] = Field(default=None, env="DATABASE_URL")
    echo: bool = Field(default=False, env="DB_ECHO")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    @validator('url', pre=True, always=True)
    def assemble_db_connection(cls, v, values):
        if isinstance(v, str):
            return v
        return (
            f"mysql+pymysql://{values.get('user')}:{values.get('password')}"
            f"@{values.get('host')}:{values.get('port')}/{values.get('name')}"
        )


class ProxySettings(BaseSettings):
    """Proxy configuration settings."""
    
    enabled: bool = Field(default=True, env="PROXY_ENABLED")
    webshare_api_key: Optional[str] = Field(default=None, env="WEBSHARE_API_KEY")
    webshare_api_url: AnyHttpUrl = Field(
        default="https://proxy.webshare.io/api/v2/proxy/list/",
        env="WEBSHARE_API_URL"
    )
    rotation_interval: int = Field(default=300, env="PROXY_ROTATION_INTERVAL")  # seconds
    max_retries: int = Field(default=3, env="PROXY_MAX_RETRIES")


class WebDriverSettings(BaseSettings):
    """WebDriver configuration settings."""
    
    chromedriver_path: Optional[str] = Field(default=None, env="CHROMEDRIVER_PATH")
    chrome_binary_path: Optional[str] = Field(default=None, env="CHROME_BINARY_PATH")
    profile_data_dir: Path = Field(default=Path("./data/profiles"), env="PROFILE_DATA_DIR")
    timeout: int = Field(default=30, env="WEBDRIVER_TIMEOUT")
    headless: bool = Field(default=False, env="HEADLESS_MODE")
    stealth_enabled: bool = Field(default=True, env="STEALTH_ENABLED")
    user_agent: Optional[str] = Field(default=None, env="USER_AGENT")
    
    @validator('profile_data_dir', pre=True)
    def validate_profile_dir(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    encryption_key: str = Field(env="ENCRYPTION_KEY")
    max_login_attempts: int = Field(default=3, env="MAX_LOGIN_ATTEMPTS")
    session_timeout: int = Field(default=3600, env="SESSION_TIMEOUT")  # seconds
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # seconds
    
    @validator('encryption_key')
    def validate_encryption_key(cls, v):
        if len(v) < 32:
            raise ValueError('Encryption key must be at least 32 characters long')
        return v


class TaskSettings(BaseSettings):
    """Task execution configuration settings."""
    
    retry_attempts: int = Field(default=3, env="TASK_RETRY_ATTEMPTS")
    retry_delay: int = Field(default=5, env="TASK_RETRY_DELAY")  # seconds
    max_concurrent: int = Field(default=5, env="MAX_CONCURRENT_TASKS")
    execution_timeout: int = Field(default=300, env="TASK_EXECUTION_TIMEOUT")  # seconds


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    dir: Path = Field(default=Path("./logs"), env="LOG_DIR")
    max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    @validator('dir', pre=True)
    def validate_log_dir(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class AppSettings(BaseSettings):
    """Main application settings."""
    
    name: str = Field(default="ProfileAutomationSystem", env="APP_NAME")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    proxy: ProxySettings = ProxySettings()
    webdriver: WebDriverSettings = WebDriverSettings()
    security: SecuritySettings = SecuritySettings()
    task: TaskSettings = TaskSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v.lower()


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> AppSettings:
    """Reload settings from environment variables."""
    global settings
    settings = AppSettings()
    return settings