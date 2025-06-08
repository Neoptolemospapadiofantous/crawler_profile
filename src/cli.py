"""
Command-line interface for the Profile Automation System.
"""

import click
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.logging import get_main_logger
from config.settings import get_settings


@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def main(ctx):
    """Profile Automation CLI - Command-line interface for profile management."""
    ctx.ensure_object(dict)
    
    # Initialize logging
    from core.logging import LoggerManager
    LoggerManager.initialize()
    
    logger = get_main_logger()
    ctx.obj['logger'] = logger


# Profile Management Commands
@main.group()
def profile():
    """Profile management commands."""
    pass


@profile.command()
@click.option('--username', required=True, help='Profile username')
@click.option('--name', help='Profile first name')
@click.option('--surname', help='Profile last name')
@click.option('--age', type=int, help='Profile age')
@click.option('--phone', help='Profile phone number')
@click.option('--nationality', help='Profile nationality')
@click.option('--typing-speed', type=int, default=2, help='Typing speed (1-10)')
@click.option('--error-rate', type=float, default=0.02, help='Typing error rate (0.0-1.0)')
@click.pass_context
def create(ctx, username, name, surname, age, phone, nationality, typing_speed, error_rate):
    """Create a new profile."""
    logger = ctx.obj['logger']
    
    click.echo(f"📝 Creating profile: {username}")
    logger.info("Profile creation requested", username=username)
    
    # Placeholder for Phase 4 implementation
    click.echo("⏳ Profile creation will be implemented in Phase 4")
    logger.info("Profile creation feature pending implementation")


@profile.command()
@click.option('--format', type=click.Choice(['table', 'json', 'simple']), 
              default='table', help='Output format')
@click.pass_context
def list(ctx, format):
    """List all profiles."""
    logger = ctx.obj['logger']
    
    click.echo("📋 Listing profiles...")
    logger.info("Profile listing requested", format=format)
    
    # Placeholder for Phase 4 implementation
    click.echo("⏳ Profile listing will be implemented in Phase 4")


@profile.command()
@click.argument('profile_id', type=int)
@click.pass_context
def show(ctx, profile_id):
    """Show detailed information about a profile."""
    logger = ctx.obj['logger']
    
    click.echo(f"👤 Showing profile: {profile_id}")
    logger.info("Profile details requested", profile_id=profile_id)
    
    # Placeholder for Phase 4 implementation
    click.echo("⏳ Profile details will be implemented in Phase 4")


@profile.command()
@click.argument('profile_id', type=int)
@click.confirmation_option(prompt='Are you sure you want to delete this profile?')
@click.pass_context
def delete(ctx, profile_id):
    """Delete a profile."""
    logger = ctx.obj['logger']
    
    click.echo(f"🗑️  Deleting profile: {profile_id}")
    logger.info("Profile deletion requested", profile_id=profile_id)
    
    # Placeholder for Phase 4 implementation
    click.echo("⏳ Profile deletion will be implemented in Phase 4")


# Task Management Commands
@main.group()
def task():
    """Task management commands."""
    pass


@task.command()
@click.argument('profile_id', type=int)
@click.option('--task-type', 
              type=click.Choice(['youtube-channel', 'login', 'crawl']),
              required=True, help='Type of task to execute')
@click.option('--params', help='Task parameters as JSON string')
@click.pass_context
def execute(ctx, profile_id, task_type, params):
    """Execute a task for a profile."""
    logger = ctx.obj['logger']
    
    click.echo(f"⚡ Executing {task_type} task for profile {profile_id}")
    logger.info("Task execution requested", 
                profile_id=profile_id, 
                task_type=task_type,
                params=params)
    
    # Placeholder for Phase 5 implementation
    click.echo("⏳ Task execution will be implemented in Phase 5")


@task.command()
@click.option('--status', type=click.Choice(['pending', 'running', 'completed', 'failed']),
              help='Filter by task status')
@click.option('--profile-id', type=int, help='Filter by profile ID')
@click.pass_context
def list_tasks(ctx, status, profile_id):
    """List tasks with optional filtering."""
    logger = ctx.obj['logger']
    
    click.echo("📋 Listing tasks...")
    logger.info("Task listing requested", status=status, profile_id=profile_id)
    
    # Placeholder for Phase 5 implementation
    click.echo("⏳ Task listing will be implemented in Phase 5")


# Configuration Commands
@main.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration."""
    logger = ctx.obj['logger']
    settings = get_settings()
    
    click.echo("⚙️  Current Configuration:")
    click.echo(f"  Environment: {settings.environment}")
    click.echo(f"  Debug: {settings.debug}")
    click.echo(f"  Database: {settings.database.host}:{settings.database.port}")
    click.echo(f"  Log Level: {settings.logging.level}")
    click.echo(f"  Proxy Enabled: {settings.proxy.enabled}")
    
    logger.info("Configuration displayed")


@config.command()
@click.pass_context
def validate(ctx):
    """Validate configuration settings."""
    logger = ctx.obj['logger']
    
    click.echo("🔍 Validating configuration...")
    logger.info("Configuration validation requested")
    
    try:
        settings = get_settings()
        
        # Basic validation
        errors = []
        
        if not settings.database.url:
            errors.append("Database URL not configured")
        
        if not settings.security.encryption_key:
            errors.append("Encryption key not configured")
        
        if errors:
            click.echo("❌ Configuration errors found:")
            for error in errors:
                click.echo(f"  - {error}")
            logger.error("Configuration validation failed", errors=errors)
        else:
            click.echo("✅ Configuration is valid")
            logger.info("Configuration validation passed")
            
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        logger.error("Configuration validation error", error=str(e))


if __name__ == "__main__":
    main()