"""
Main entry point for the AI Project Orchestration System

This module serves as the main entry point for the application, handling:
- System initialization and startup
- Component setup and configuration
- Application lifecycle management
- Top-level error handling

"""

import typer

from src.cli.entrypoint import app
from src.utils.logging import setup_logger
from src.config import settings
from src.cli.cli_enrich import display_error

# Setup logger using configuration
logger = setup_logger(
    "main",
    settings.logging.module_levels.get("main", settings.logging.level)
)

def main():
    """
    Main entry point for the application
    
    Initializes the CLI application and handles top-level errors
    """
    try:
        logger.info("[Main] Starting AI Project Orchestration System")
        app()
    except Exception as e:
        display_error(f"[Main] Application error: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    main() 