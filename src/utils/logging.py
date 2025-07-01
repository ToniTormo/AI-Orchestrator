"""
Logging configuration for the AI Project Orchestration System

This module provides centralized logging configuration with:
- Console and file handlers with rotation
- Module-specific log levels from environment variables
- Configurable formatters for different output targets
"""

import os
import logging
import ast
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configuration constants
DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEFAULT_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '5242880'))  # 5MB
DEFAULT_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Set up a logger with console and file handlers
    
    Args:
        name: Logger name
        level: Log level (defaults to module-specific level or LOG_LEVEL from .env)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory in project root
    log_dir = _get_project_log_directory()
    log_dir.mkdir(exist_ok=True)
    
    # Get log level - priority: parameter > module-specific > default
    if level is None:
        level = _get_module_level(name, DEFAULT_LOG_LEVEL)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Add handlers
    _add_console_handler(logger)
    _add_file_handler(logger, log_dir)
    
    return logger

def _get_project_log_directory() -> Path:
    """
    Get the project root directory for logs
    
    Returns:
        Path to logs directory in project root
    """
    # Get the project root directory (where this file is located relative to src/utils)
    current_file = Path(__file__)  # src/utils/logging.py
    project_root = current_file.parent.parent.parent  # Go up: utils -> src -> project_root
    return project_root / "logs"

def _get_module_level(name: str, default_level: str) -> str:
    """
    Get the log level for a specific module
    
    Args:
        name: Module name
        default_level: Default log level
        
    Returns:
        Log level for the module
    """
    # Try to get module levels from environment
    env_module_levels = os.getenv('LOG_MODULE_LEVELS')
    if not env_module_levels:
        return default_level
        
    try:
        parsed_levels = ast.literal_eval(env_module_levels)
        if not isinstance(parsed_levels, dict):
            raise ValueError(f"LOG_MODULE_LEVELS must be a dictionary, got {type(parsed_levels)}")
        
        # Check for exact match first
        if name in parsed_levels:
            return parsed_levels[name]
        
        # Check for partial matches (e.g., "project" matches "project.coordinator")
        for module_prefix, level in parsed_levels.items():
            if name.startswith(module_prefix):
                return level
                
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid LOG_MODULE_LEVELS format: {str(e)}")
    
    return default_level

def _add_console_handler(logger: logging.Logger):
    """Add console handler to logger"""
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

def _add_file_handler(logger: logging.Logger, log_dir: Path):
    """Add rotating file handler to logger with Windows-friendly configuration"""
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
    main_log = log_dir / "logs.log"
    
    # Use delay=True to defer file opening and mode='a' for Windows compatibility
    main_handler = RotatingFileHandler(
        main_log,
        maxBytes=DEFAULT_MAX_BYTES,
        backupCount=DEFAULT_BACKUP_COUNT,
        mode='a',
        delay=True
    )
    main_handler.setFormatter(file_formatter)
    logger.addHandler(main_handler)