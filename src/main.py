"""
Main entry point for the Profile Automation System.
"""

import sys
import click
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.logging import get_logger_manager, get_main_logger
from config.settings import get_settings


def setup_application():
    """Initialize the application."""
    try:
        # Initialize logging
        get_logger_manager()
        logger = get_main_logger()
        
        # Load and validate settings
        settings = get_settings()
        logger.info(
            "Application starting",
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment
        )
        
        # Validate critical settings
        if not settings.database_url:
            logger.error("Database URL not configured")
            sys.exit(1)

        if not settings.encryption_key:
            logger.error("Encryption key not configured")
            sys.exit(1)
        
        logger.info("Application setup completed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to setup application: {e}")
        sys.exit(1)


@click.group()
@click.version_option(version="1.0.0")
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
def main(debug, config):
    """Profile Automation System - Automated profile management and task execution."""
    if debug:
        import os
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    if config:
        import os
        os.environ['CONFIG_FILE'] = config
    
    setup_application()


@main.command()
def init():
    """Initialize the application (create database, setup directories)."""
    logger = get_main_logger()
    logger.info("Initializing application...")
    
    try:
        # Create necessary directories
        settings = get_settings()
        
        # Create data directories
        settings.profile_storage_path.mkdir(parents=True, exist_ok=True)
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database (placeholder - will implement in Phase 2)
        logger.info("Database initialization will be implemented in Phase 2")
        
        click.echo("✅ Application initialized successfully!")
        logger.info("Application initialization completed")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        click.echo(f"❌ Initialization failed: {e}")
        sys.exit(1)


@main.command()
def status():
    """Show application status and configuration."""
    logger = get_main_logger()
    settings = get_settings()
    
    click.echo(f"🚀 {settings.app_name} v{settings.app_version}")
    click.echo(f"Environment: {settings.environment}")
    click.echo(f"Debug mode: {settings.debug}")
    click.echo(f"Log level: {settings.log_level}")
    click.echo(
        f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    click.echo(f"Profile directory: {settings.profile_storage_path}")
    click.echo(f"Proxy enabled: {settings.proxy_enabled}")
    
    # Check component status
    click.echo("\n📊 Component Status:")
    
    # Database connection (placeholder)
    click.echo("  Database: ⏳ Not implemented yet")
    
    # WebDriver availability
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        if settings.chromedriver_path and Path(settings.chromedriver_path).exists():
            click.echo("  ChromeDriver: ✅ Available")
        else:
            click.echo("  ChromeDriver: ❌ Not configured or not found")
    except ImportError:
        click.echo("  WebDriver: ❌ Selenium not installed")
    
    # Proxy service
    if settings.proxy_enabled and settings.proxy_api_key:
        click.echo("  Proxy Service: ✅ Configured")
    else:
        click.echo("  Proxy Service: ❌ Not configured")
    
    logger.info("Status check completed")


@main.command()
@click.option('--component', type=click.Choice(['all', 'database', 'webdriver', 'proxy']), 
              default='all', help='Component to test')
def test(component):
    """Test application components."""
    logger = get_main_logger()
    logger.info("Running component tests", component=component)
    
    click.echo(f"🔧 Testing {component} component(s)...")
    
    if component in ['all', 'webdriver']:
        click.echo("  WebDriver test: ⏳ Will be implemented in Phase 6")
    
    if component in ['all', 'database']:
        click.echo("  Database test: ⏳ Will be implemented in Phase 2")
    
    if component in ['all', 'proxy']:
        click.echo("  Proxy test: ⏳ Will be implemented in Phase 7")
    
    click.echo("✅ Component tests completed!")


if __name__ == "__main__":
    main()