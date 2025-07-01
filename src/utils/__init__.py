"""
Utils Module

Utility functions and base classes for the AI Project Orchestration System
"""

from .logging import setup_logger
from .exceptions_control import (
    create_error,
    BaseServiceError,
    UserAbortError,
    GitServiceError,
    OrchestrationError,
    AgentError,
    ValidationError,
    ProjectError,
    EmailNotificationError,
    MockServiceError
)

__all__ = [
    # Logging
    "setup_logger",
    # Exceptions
    "create_error",
    "BaseServiceError",
    "UserAbortError",
    "GitServiceError",
    "OrchestrationError",
    "AgentError",
    "ValidationError",
    "ProjectError",
    "EmailNotificationError",
    "MockServiceError"
] 