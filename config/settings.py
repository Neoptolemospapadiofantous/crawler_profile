"""
Application configuration using Pydantic settings management.
Handles environment variables, validation, and type safety.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="Profile Automation System", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Runtime environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Security settings
    secret_key: str = Field(default="", description="Application secret key")
    encryption_key: str = Field(default="", description="Fernet encryption key")
    
    # Proxy settings
    proxy_enabled: bool = Field(default=False, description="Enable proxy usage")
    proxy_api_key: Optional[str] = Field(default=None, description="Proxy service API key")
    proxy_api_url: Optional[str] = Field(default=None, description="Proxy service API URL")
    
    # WebDriver settings
    webdriver_type: str = Field(default="chrome", description="WebDriver type (chrome/firefox)")
    chromedriver_path: Optional[str] = Field(default=None, description="Path to ChromeDriver")
    chrome_binary_path: Optional[str] = Field(default=None, description="Path to Chrome binary")
    webdriver_headless: bool = Field(default=False, description="Run browser in headless mode")
    webdriver_timeout: int = Field(default=30, description="WebDriver timeout in seconds")
    
    # Profile settings
    profile_storage_path: Path = Field(default=Path("profiles"), description="Profile storage directory")
    max_concurrent_profiles: int = Field(default=5, description="Maximum concurrent profiles")
    
    # Task settings
    task_retry_attempts: int = Field(default=3, description="Task retry attempts")
    task_retry_delay: int = Field(default=60, description="Task retry delay in seconds")
    task_timeout: int = Field(default=300, description="Task timeout in seconds")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    log_dir: Path = Field(default=Path("logs"), description="Log directory")
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate Fernet encryption key."""
        if v and len(v) != 44:
            raise ValueError("Encryption key must be 44 characters (Fernet key)")
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is set in production."""
        if not v:
            # Generate a random key for development
            import secrets
            return secrets.token_urlsafe(32)
        return v
    
    @field_validator("profile_storage_path", "log_dir")
    @classmethod
    def create_directory(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_webdriver_options(self) -> Dict[str, Any]:
        """Get WebDriver configuration options."""
        return {
            "headless": self.webdriver_headless,
            "timeout": self.webdriver_timeout,
            "binary_path": self.chrome_binary_path,
            "driver_path": self.chromedriver_path,
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


# Global settings instance
settings = Settings()

# For backward compatibility
def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


class WebDriverSettings:
    """WebDriver specific settings and validation."""
    
    @staticmethod
    def get_chrome_options():
        """Get Chrome-specific options."""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        
        # Basic options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Anti-detection options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Performance options
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")
        
        if settings.webdriver_headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        
        return options
    
    @staticmethod
    def validate_chrome_setup() -> bool:
        """Validate Chrome and ChromeDriver are available."""
        import shutil
        import subprocess
        
        # Check Chrome browser
        chrome_paths = [
            settings.chrome_binary_path,
            shutil.which("google-chrome"),
            shutil.which("chrome"),
            shutil.which("chromium"),
        ]
        
        chrome_found = any(path and os.path.exists(path) for path in chrome_paths if path)
        
        # Check ChromeDriver
        driver_paths = [
            settings.chromedriver_path,
            shutil.which("chromedriver"),
        ]
        
        driver_found = any(path and os.path.exists(path) for path in driver_paths if path)
        
        return chrome_found and driver_found