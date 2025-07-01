"""
Execution Tests Infrastructure Module

Provides testing utilities for validating implementation execution results.
These tests verify that code changes and implementations were applied correctly
in cloned repositories, NOT for testing the orchestrator project itself.
"""

from .test_manager import TestManager, TestManagerError
from .test_service import AutomatedTestingService, TestingError
from .test_implementation import ImplementationValidator
from .test_suite_runner import TestSuiteRunner
from .test_results_analyzer import TestResultsAnalyzer
# from .test_history_manager import TestHistoryManager

__all__ = [
    "TestManager",
    "TestManagerError",
    "AutomatedTestingService", 
    "TestingError",
    "ImplementationValidator",
    "TestSuiteRunner",
    "TestResultsAnalyzer", 
    # "TestHistoryManager"
] 