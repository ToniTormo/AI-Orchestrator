"""
Task Management package

Handles task planning, prioritization, and categorization for the application.

Components:
- TaskManager: Plans and distributes tasks to specialized AI agents
- TaskPrioritizer: Prioritizes tasks based on complexity and dependencies  
- TaskCategorizer: Intelligent task categorization (now local to tasks module)
"""

from .task_manager import TaskManager
from .task_prioritizer import TaskPrioritizer
from .task_categorizer import TaskCategorizer

__all__ = [
    'TaskManager',
    'TaskPrioritizer', 
    'TaskCategorizer',
] 