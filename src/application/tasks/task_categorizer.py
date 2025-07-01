"""
Task Categorizer

Handles task categorization based on content analysis and project technologies.
Responsibility: Categorize task recommendations to determine which agent (frontend/backend) should handle them.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, TaskManagerError
from src.config import settings



class TaskCategorizer:
    """
    Specialized service for categorizing tasks based on content analysis.
    Uses configuration from task_categorization.yaml and project context to determine appropriate categories.
    Currently returns 'frontend' or 'backend' for agent assignment, but designed to be scalable for future agents.
    
    Responsibility: Take task recommendations and decide which specialized AI agent should execute them.
    Uses ALL technology categories detected by TechDetector for comprehensive analysis.
    """
    
    def __init__(self):
        """Initialize the task categorizer"""
        self.logger = setup_logger(
            "task.categorizer",
            settings.logging.module_levels.get("task", settings.logging.level)
        )
        self.config = self._load_config()
        
        self.logger.info("[TaskCategorizer] Initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load task categorization configuration from the correct config file"""
        try:
            config_path = Path(__file__).parent / "config" / "task_categorization.yaml"
            
            if not config_path.exists():
                raise FileNotFoundError(f"[TaskCategorizer] Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
                if not config:
                    raise create_error(RuntimeError, "Configuration file is empty or invalid", "TaskCategorizer")
                
                task_config = config.get('task_categorization')
                if not task_config:
                    raise create_error(RuntimeError, "task_categorization section not found in config file", "TaskCategorizer")
                
                return task_config
                
        except Exception as e:
            raise create_error(RuntimeError, f"Failed to load configuration: {e}", "TaskCategorizer")
    
    def determine_task_category(self, recommendation: str, tech_stack: Dict[str, Any] = None) -> str:
        """
        Determines the appropriate agent category for a task based on content and technologies.
        Returns ONLY 'frontend' or 'backend' for clear agent assignment.
        
        Args:
            recommendation: Task recommendation text
            tech_stack: Project tech stack (optional)
            
        Returns:
            Agent category
        """
        if not recommendation:
            raise create_error(ValueError, "Recommendation cannot be empty", "TaskCategorizer")
                
        recommendation_lower = recommendation.lower()
        self.logger.debug(f"[TaskCategorizer] Categorizing task: {recommendation[:100]}...")
        
        try:
            # Calculate weights for both categories
            task_scores = self._calculate_category_scores(recommendation_lower, tech_stack)
            
            # Simple winner determination: highest score wins
            if task_scores["frontend"] > task_scores["backend"]:
                category = "frontend"
            elif task_scores["backend"] >= task_scores["frontend"]:
                category = "backend"
            
            self.logger.debug(f"[TaskCategorizer] Task categorized as: {category}")
            return category
            
        except Exception as e:
            raise create_error(RuntimeError, f"Failed to categorize task: {str(e)}", "TaskCategorizer")
    
    def _calculate_category_scores(self, recommendation_lower: str, tech_stack: Dict[str, Any] = None) -> Dict[str, int]:
        """Calculate scores for frontend and backend categories"""
        task_scores = {
            "frontend": self._calculate_category_score(recommendation_lower, "frontend"),
            "backend": self._calculate_category_score(recommendation_lower, "backend")
        }
        
        # Consider project tech stack if provided
        if tech_stack:
            self._adjust_scores_by_tech_stack(task_scores, recommendation_lower, tech_stack)
        
        self.logger.debug(f"[TaskCategorizer] Category scores: {task_scores}")
        return task_scores
    
    def _calculate_category_score(self, text: str, category: str) -> int:
        """Calculate the score for a specific category based on term matches"""
        total_score = 0
        categories_config = self.config.get("categories")
        
        if not categories_config:
            raise create_error(RuntimeError, "Categories configuration not found", "TaskCategorizer")
            
        category_config = categories_config.get(category)
        if not category_config:
            raise create_error(RuntimeError, f"Category '{category}' configuration not found", "TaskCategorizer")
        
        for group_name, group_config in category_config.items():
            if isinstance(group_config, dict) and "weight" in group_config and "terms" in group_config:
                weight = group_config["weight"]
                terms = group_config["terms"]
                
                for term in terms:
                    if term in text:
                        total_score += weight
        
        return total_score
    
    def _adjust_scores_by_tech_stack(self, scores: Dict[str, int], text: str, tech_stack: Dict[str, Any]):
        """
        Adjust scores based on detected technologies using YAML weights.
        Simple approach: search YAML terms in text + detected technologies, sum weights.
        """
        text_lower = text.lower()
        
        # Get all detected technologies as a flat list
        all_detected_techs = []
        for technologies in tech_stack.values():
            all_detected_techs.extend([str(tech).lower() for tech in technologies])
        
        # Search YAML terms in text and detected technologies
        categories_config = self.config.get("categories", {})
        
        for category_name, category_config in categories_config.items():
            if not isinstance(category_config, dict):
                continue
                
            # Check each group in this category (frameworks, languages, etc.)
            for group_name, group_config in category_config.items():
                if not isinstance(group_config, dict) or "weight" not in group_config or "terms" not in group_config:
                    continue
                    
                weight = group_config["weight"]
                terms = group_config["terms"]
                
                # Check if any YAML term appears in text or detected technologies
                for term in terms:
                    term_lower = term.lower()
                    
                    # Search in task text
                    if term_lower in text_lower:
                        scores[category_name] += weight
                    
                    # Search in detected technologies
                    elif any(term_lower in tech or tech in term_lower for tech in all_detected_techs):
                        scores[category_name] += weight
   