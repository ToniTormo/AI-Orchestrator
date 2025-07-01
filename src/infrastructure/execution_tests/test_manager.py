"""
Execution Test Manager

Manages test execution for verifying implementation results in cloned repositories.
These tests validate that code changes were applied correctly, NOT project unit tests.
"""

from typing import Dict, List, Any
from src.infrastructure.services import SimpleAsyncService
from src.utils.exceptions_control import create_error
from .test_implementation import ImplementationValidator
from .test_suite_runner import TestSuiteRunner
from .test_results_analyzer import TestResultsAnalyzer

class TestManagerError(Exception):
    """Raised when there are issues with test management"""
    pass

class TestManager(SimpleAsyncService):
    """
    Main coordinator for execution tests that validate implementation results.
    Verifies that code changes were applied correctly in cloned repositories.
    """

    def __init__(self):
        """Initialize the execution test manager"""
        super().__init__("execution_tests.manager")
        try:
            self.implementation_validator = ImplementationValidator()
            self.suite_runner = TestSuiteRunner()
            self.results_analyzer = TestResultsAnalyzer()
            self.logger.info("[TestManager] Successfully initialized execution test manager")
        except Exception as e:
            raise create_error(TestManagerError, f"Failed to initialize execution test manager: {e}", "TestManager")

    async def _initialize_impl(self):
        """Initialize the execution test manager implementation"""
        pass

    async def _shutdown_impl(self):
        """Shutdown the execution test manager implementation"""
        pass

    async def run_all_tests(self, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all execution tests on implementation results.
        This method first runs implementation validation tests, then additional test suites.
        
        Args:
            implementation_results: Results from agent implementations
            
        Returns:
            Dictionary with complete test results
        """
        try:
            results = {
                "frontend": {"passed": 0, "failed": 0, "total": 0, "failed_tests": []},
                "backend": {"passed": 0, "failed": 0, "total": 0, "failed_tests": []}
            }
            
            # STEP 1: Run implementation validation tests FIRST for each EXECUTION component
            # Note: only frontend and backend execute tasks, analyzer only analyzes
            for component in ["frontend", "backend"]:
                if component in implementation_results:
                    self.logger.info(f"[TestManager] Running implementation validation for {component}")
                    
                    # Run implementation validation tests first
                    validation_results = await self.run_implementation_validation(
                        component, 
                        implementation_results[component]
                    )
                    
                    # Add validation results to component results
                    self._merge_validation_results(results[component], validation_results, component)
                    
                    # STEP 2: Run additional test suites if validation passed
                    if results[component]["failed"] == 0:
                        suite_results = await self.suite_runner.run_component_test_suite(
                            component,
                            implementation_results[component]
                        )
                        
                        # Merge suite results
                        self._merge_suite_results(results[component], suite_results)
                    else:
                        self.logger.warning(f"[TestManager] Skipping additional tests for {component} due to validation failures")
                else:
                    self.logger.warning(f"[TestManager] No implementation found for {component}")
            
            # Check if all tests passed
            all_passed = all(
                component_results["failed"] == 0 
                for component_results in results.values()
            )
            
            self.logger.info(f"[TestManager] All execution tests completed. All passed: {all_passed}")
            return {
                "results": results,
                "all_passed": all_passed
            }
            
        except Exception as e:
            raise create_error(TestManagerError, f"Error running execution tests: {e}", "TestManager")

    async def run_implementation_validation(self, component: str, implementation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run implementation validation tests for a specific component.
        This is the core validation that verifies implementation execution.
        
        Args:
            component: The component to validate
            implementation_result: The implementation result to validate
            
        Returns:
            List of validation test results
        """
        test_results = []
        
        try:
            # Get validation cases from the implementation validator
            validation_cases = self.implementation_validator.get_validation_cases(component)
            
            # Run each validation case
            for validation_case in validation_cases:
                try:
                    # Execute validation using the implementation validator
                    passed = await self.implementation_validator.execute_validation(validation_case, implementation_result)
                    
                    # Record result
                    test_results.append({
                        'name': validation_case.get('name', 'Unknown validation'),
                        'passed': passed,
                        'error': None if passed else 'Implementation validation failed'
                    })
                    
                except Exception as e:
                    self.logger.error(f"[TestManager] Validation {validation_case.get('name', 'Unknown')} failed: {e}")
                    test_results.append({
                        'name': validation_case.get('name', 'Unknown validation'),
                        'passed': False,
                        'error': str(e)
                    })
            
            self.logger.info(f"[TestManager] Completed {len(test_results)} validations for {component}")
            return test_results
            
        except Exception as e:
            self.logger.error(f"[TestManager] Error running validations for {component}: {e}")
            return []

    def _merge_validation_results(self, component_results: Dict[str, Any], validation_results: List[Dict[str, Any]], component: str):
        """
        Merge validation results into component results
        
        Args:
            component_results: Component results dictionary to merge into
            validation_results: Validation results to merge
            component: Component name for logging
        """
        for validation_result in validation_results:
            component_results["total"] += 1
            if validation_result["passed"]:
                component_results["passed"] += 1
            else:
                component_results["failed"] += 1
                component_results["failed_tests"].append({
                    "name": validation_result["name"],
                    "error": validation_result.get("error", "Validation failed"),
                    "component": component,
                    "type": "validation"
                })

    def _merge_suite_results(self, component_results: Dict[str, Any], suite_results: Dict[str, Any]):
        """
        Merge suite results into component results
        
        Args:
            component_results: Component results dictionary to merge into
            suite_results: Suite results to merge
        """
        component_results["passed"] += suite_results["passed"]
        component_results["failed"] += suite_results["failed"]
        component_results["total"] += suite_results["total"]
        component_results["failed_tests"].extend(suite_results["failed_tests"])

    async def analyze_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test results and generate insights
        
        Args:
            results: Test results to analyze
            
        Returns:
            Analysis results
        """
        return await self.results_analyzer.analyze_test_results(results)
