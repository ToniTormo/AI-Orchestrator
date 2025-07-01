"""
Mock service for testing and development
"""

from typing import Dict, List, Any
from unittest.mock import Mock
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, MockServiceError
from src.config import settings

class MockService:
    """Service for handling mock operations"""
    
    def __init__(self):
        """Initialize the mock service"""
        self.logger = setup_logger(
            "mocks.service",
            settings.logging.module_levels.get("mocks", settings.logging.level)
        )
        
        self.enabled = settings.mock.enabled
        if self.enabled:
            self.logger.info("[MockService] Mock mode enabled")
    
    def is_enabled(self) -> bool:
        """Check if mock mode is enabled"""
        return self.enabled
    
    def get_mock_merge_request(self, title: str, description: str) -> Dict[str, Any]:
        """Get mock merge request data"""
        if not title or not description:
            raise create_error(MockServiceError, "Title and description are required for mock merge request", "MockService")
            
        return {
            "html_url": "https://github.com/mockuser/mock_repo/pull/1",
            "number": 1,
            "title": title,
            "body": description
        }
    
    def get_mock_commit_result(self) -> bool:
        """Get mock commit result"""
        return True
    
    def get_mock_push_result(self) -> bool:
        """Get mock push result"""
        return True

    def get_mock_repo(self, repo_path: str):
        """Get mock repository object"""
        if not repo_path:
            raise create_error(MockServiceError, "Repository path is required for mock repository", "MockService")
            
        mock_repo = Mock()
        mock_repo.working_dir = repo_path
        self.logger.info(f"[MockService] Created mock repository for path: {repo_path}")
        return mock_repo

    def get_mock_task_results(self, task_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get mock results for task execution
        
        Args:
            task_plan: List of tasks to simulate
            
        Returns:
            Dictionary with simulated implementation and test results
        """
        if not task_plan:
            raise create_error(MockServiceError, "Task plan cannot be empty for mock task results", "MockService")
            
        self.logger.info("[MockService] Generating mock task results")
        results = {
            "implementation_results": {},
            "test_results": {
                "results": {},
                "all_passed": True
            }
        }
        
        # Generate mock implementation results
        for task in task_plan:
            task_id = task.get('id')
            if not task_id:
                raise create_error(MockServiceError, "Task must have an 'id' field", "MockService")
                
            results["implementation_results"][task_id] = {
                'status': 'success',
                'result': {
                    'message': f"Simulated successful execution of task {task_id}",
                    'changes': []
                },
                'component': task.get('category', 'unknown')
            }
        
        # Generate mock test results
        results["test_results"] = {
            "results": {
                "frontend": {"passed": 1, "failed": 0, "total": 1, "failed_tests": []},
                "backend": {"passed": 1, "failed": 0, "total": 1, "failed_tests": []}
            },
            "all_passed": True
        }
        
        self.logger.info("[MockService] Generated mock task results")
        return results 