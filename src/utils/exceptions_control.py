"""
Custom exceptions for the AI Project Orchestration System

This module provides centralized exception handling with:
- Standardized error creation and logging
- Domain-specific exception classes
- Consistent error reporting across the application
"""

from src.utils.logging import setup_logger
from typing import Type

logger = setup_logger("exceptions")

def create_error(error_type: Type[Exception], message: str, service_name: str = "Service") -> Exception:
    """
    Create and log an error with consistent formatting
    
    Args:
        error_type: Type of exception to create
        message: Error message describing the issue
        service_name: Name of the service raising the error for context
        
    Returns:
        Exception instance ready to be raised
    """
    logger.error(f"[{service_name}] {message}")
    return error_type(message)

# Base exception classes
class BaseServiceError(Exception):
    """Base exception class for all service-related errors"""
    pass

# Domain-specific exception classes
class UserAbortError(BaseServiceError):
    """Exception raised when user explicitly aborts an operation"""
    pass

class GitServiceError(BaseServiceError):
    """Exception for Git repository operations and version control errors"""
    pass

class OrchestrationError(BaseServiceError):
    """Exception for orchestration workflow and coordination errors"""
    pass

class AgentError(BaseServiceError):
    """Exception for AI agent operations and communication errors"""
    pass

class ValidationError(BaseServiceError):
    """Exception for input validation and configuration errors"""
    pass

class ProjectError(BaseServiceError):
    """Exception for project analysis and processing errors"""
    pass

class TaskManagerError(BaseServiceError):
    """Exception for task management errors"""
    pass

class OpenAIServiceError(BaseServiceError):
    """Base class for OpenAI service errors"""
    pass

class EmailNotificationError(BaseServiceError):
    """Exception for email notification service errors"""
    pass

class MockServiceError(BaseServiceError):
    """Exception for mock service errors"""
    pass