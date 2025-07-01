"""
Automated Execution Testing Service

Provides testing capabilities for validating implementation execution results.
These tests verify that code changes were applied correctly in cloned repositories,
NOT for testing the orchestrator project itself.
"""

from typing import Dict, List, Any
from src.infrastructure.services import SimpleAsyncService
from src.utils.exceptions_control import create_error
from src.infrastructure.execution_tests.test_manager import TestManager

class TestingError(Exception):
    """Raised when there are issues with testing operations"""
    pass

class AutomatedTestingService(SimpleAsyncService):
    """
    Service for handling execution testing operations.
    Validates that implementations were applied correctly in cloned repositories.
    """

    def __init__(self, test_manager: TestManager = None):
        """
        Initialize the automated execution testing service
        
        Args:
            test_manager: The test manager instance to use (optional, will create if not provided)
        """
        super().__init__("execution_tests.service")
        try:
            self.test_manager = test_manager or TestManager()
            self.logger.info("[TestingService] Successfully initialized execution testing service")
        except Exception as e:
            raise create_error(TestingError, f"Failed to initialize execution testing service: {e}", "TestingService")

    async def _initialize_impl(self):
        """Initialize the testing service implementation"""
        await self.test_manager.initialize()

    async def _shutdown_impl(self):
        """Shutdown the testing service implementation"""
        if hasattr(self.test_manager, 'shutdown'):
            await self.test_manager.shutdown()

    async def run_implementation_tests(self, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run execution tests on implementation results to validate they were applied correctly.
        
        Args:
            implementation_results: Dictionary containing implementation results by task_id
                                  Format: {task_id: {status, result, component}, ...}
            
        Returns:
            Dictionary containing test results and overall status
        """
        self.logger.info("[TestingService] Starting execution testing workflow")
        
        try:
            if not implementation_results:
                self.logger.warning("[TestingService] No implementation results provided for testing")
                return {
                    "results": {},
                    "all_passed": True,
                    "message": "No implementations to test"
                }

            # Reorganize results by component for testing_manager
            component_results = self._reorganize_results_by_component(implementation_results)
            
            # Use the integrated run_all_tests method which now includes validation first
            test_results = await self.test_manager.run_all_tests(component_results)
            
            # Analyze the results 
            analysis = await self.test_manager.analyze_test_results(test_results["results"])
            
            return {
                "results": test_results["results"],
                "all_passed": test_results["all_passed"],
                "analysis": analysis,
                "summary": self._create_test_summary(test_results["results"])
            }
            
        except Exception as e:
            self.logger.error(f"[TestingService] Error during execution testing: {e}")
            raise create_error(TestingError, f"Execution testing failed: {e}", "TestingService")

    def _reorganize_results_by_component(self, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reorganize implementation results from task_id structure to component structure
        Note: Only handles execution components (frontend, backend), not analyzer
        
        Args:
            implementation_results: {task_id: {status, result, component}, ...}
            
        Returns:
            component_results: {component: implementation_data, ...}
        """
        component_results = {}
        
        for task_id, task_result in implementation_results.items():
            component = task_result.get('component')
            
            # Only include EXECUTION components that actually execute tasks
            # Note: analyzer generates recommendations but doesn't execute tasks
            if component in ['frontend', 'backend']:
                if component not in component_results:
                    # Initialize component entry with combined data from all tasks of this component
                    component_results[component] = {
                        'status': 'success',  # Will be updated if any task fails
                        'result': {
                            'files_modified': [],
                            'tasks_completed': [],
                            'component_name': component
                        }
                    }
                
                # Update component status (if any task fails, component fails)
                if task_result.get('status') != 'success':
                    component_results[component]['status'] = 'failed'
                    if 'error' not in component_results[component]:
                        component_results[component]['error'] = task_result.get('error', 'Unknown error')
                
                # Aggregate task results
                component_results[component]['result']['tasks_completed'].append(task_id)
                
                # Aggregate files modified
                if 'result' in task_result and isinstance(task_result['result'], dict):
                    task_files = task_result['result'].get('files_modified', [])
                    component_results[component]['result']['files_modified'].extend(task_files)
            else:
                self.logger.warning(f"[TestingService] Unknown execution component '{component}' for task {task_id}")
        
        self.logger.debug(f"[TestingService] Reorganized results for execution components: {list(component_results.keys())}")
        return component_results

    def _create_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of execution test results
        
        Args:
            results: Test results dictionary
            
        Returns:
            Summary dictionary
        """
        total_passed = sum(component["passed"] for component in results.values())
        total_failed = sum(component["failed"] for component in results.values())
        total_tests = sum(component["total"] for component in results.values())
        
        components_tested = len([comp for comp, res in results.items() if res["total"] > 0])
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "components_tested": components_tested,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        }

    async def get_test_history(self) -> List[Dict[str, Any]]:
        """
        Get execution test history
        
        Returns:
            List of historical test execution results
        """
        self.logger.info("[TestingService] Retrieving execution test history")
        return self.test_manager.get_test_history()

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the execution testing service
        
        Returns:
            Health status dictionary
        """
        try:
            return {
                "service": "AutomatedTestingService",
                "status": "healthy",
                "test_manager_available": self.test_manager is not None,
                "message": "Execution testing service is operational"
            }
        except Exception as e:
            return {
                "service": "AutomatedTestingService", 
                "status": "unhealthy",
                "error": str(e),
                "message": "Execution testing service has issues"
            }

 