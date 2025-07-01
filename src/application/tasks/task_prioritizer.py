"""
Task Prioritizer Utility

Handles the logic for prioritizing tasks based on priority levels (high, medium, low).
Simplified to work with the new streamlined Task structure without dependencies or complexity.
"""

from src.utils.logging import setup_logger
from src.config import settings
from src.utils.exceptions_control import create_error, TaskManagerError

class TaskPrioritizer:
    """
    Utility class for prioritizing tasks by priority levels only.
    Simplified to handle basic priority ordering without dependencies or complexity calculations.
    """
    
    def __init__(self):
        """Initialize the task prioritizer"""
        self.logger = setup_logger(
            "task.prioritizer",
            settings.logging.module_levels.get("task", settings.logging.level)
        )
    
    def determine_priority(self, recommendation: str) -> str:
        """
        Determine priority based on recommendation content with improved logic
        
        Args:
            recommendation: Task recommendation text
            
        Returns:
            Priority level (high, medium, low)
        """
        if not recommendation:
            raise create_error(ValueError, "Recommendation cannot be empty", "TaskPrioritizer")
            
        recommendation_lower = recommendation.lower()
        
        # High priority keywords (critical functionality, bugs, security)
        high_priority_terms = [
            "critical", "urgent", "important", "security", "fix", "bug", 
            "error", "crash", "broken", "essential", "core", "main",
            "authentication", "login", "api", "database", "connection",
            "integration", "endpoint", "service"
        ]
        
        # Low priority keywords (enhancements, polish, future)
        low_priority_terms = [
            "nice to have", "optional", "enhancement", "improvement", 
            "polish", "cosmetic", "future", "later", "minor", "style",
            "ui improvement", "visual", "layout", "color", "font"
        ]
        
        # Check for explicit priority indicators (order matters - high first)
        if any(term in recommendation_lower for term in high_priority_terms):
            return "high"
        
        if any(term in recommendation_lower for term in low_priority_terms):
            return "low"
        
        # Default to medium priority for implementation tasks
        return "medium"
    