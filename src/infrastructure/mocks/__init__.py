"""
Mock module initialization
"""

from .mock_openai import MockOpenAIService
from src.config import settings

def is_mock_enabled() -> bool:
    """Check if mocks are enabled"""
    return settings.mock.enabled

__all__ = [
    'MockOpenAIService',
    'is_mock_enabled'
] 