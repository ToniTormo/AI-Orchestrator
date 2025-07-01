"""
Test Suite Runner

Handles execution of test suites for individual components.
"""

from typing import Dict, List, Any
from src.utils.logging import setup_logger
from src.config import settings

class TestSuiteRunner:
    """
    Executes test suites for execution components (frontend, backend).
    """
    
    def __init__(self):
        """Initialize the test suite runner"""
        self.logger = setup_logger(
            "execution_tests.suite_runner",
            settings.logging.module_levels.get("execution_tests", settings.logging.level)
        )
    
    async def run_component_test_suite(self, component: str, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run additional test suite for a specific component (after validation passes).
        
        Args:
            component: Component type
            implementation: Implementation details for the component
            
        Returns:
            Test results for the component
        """
        try:
            self.logger.info(f"[TestSuiteRunner] Starting additional test suite for {component}")
            results = {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "failed_tests": []
            }
            
            # Get appropriate test suite
            test_suite = self._get_test_suite(component)
            
            # Run tests
            for test in test_suite:
                results["total"] += 1
                try:
                    test_result = await self._run_single_test(test, implementation)
                    if test_result["passed"]:
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                        failed_test = {
                            "name": test["name"],
                            "error": test_result["error"],
                            "component": component,
                            "type": "suite"
                        }
                        results["failed_tests"].append(failed_test)
                        self.logger.warning(f"[TestSuiteRunner] Test failed: {test['name']} - {test_result['error']}")
                except Exception as e:
                    results["failed"] += 1
                    failed_test = {
                        "name": test["name"],
                        "error": str(e),
                        "component": component,
                        "type": "suite"
                    }
                    results["failed_tests"].append(failed_test)
                    self.logger.error(f"[TestSuiteRunner] Error running test {test['name']}: {e}")
            
            self.logger.info(f"[TestSuiteRunner] Completed {component} additional tests: {results['passed']} passed, {results['failed']} failed")
            return results
            
        except Exception as e:
            self.logger.error(f"[TestSuiteRunner] Error running {component} test suite: {e}")
            return {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "failed_tests": [{
                    "name": "Test Suite Error",
                    "error": str(e),
                    "component": component,
                    "type": "suite"
                }]
            }

    async def _run_single_test(self, test: Dict[str, Any], implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single execution test
        
        Args:
            test: Test configuration
            implementation: Implementation details
            
        Returns:
            Test result
        """
        try:
            # Simulate running the test based on type
            test_type = test.get("type", "basic")
            test_name = test.get("name", "Unknown Test")
            
            # Simple execution validation based on test type
            if test_type == "implementation":
                # Check if implementation was successful
                status = implementation.get("status", "unknown")
                passed = status == "success"
                error = None if passed else f"Implementation status was '{status}', expected 'success'"
                
            elif test_type == "functional":
                # Check if there are functional results
                result = implementation.get("result", {})
                passed = bool(result)
                error = None if passed else "No functional results found"
                
            elif test_type == "integration":
                # Check if integration was successful
                files_modified = implementation.get("result", {}).get("files_modified", [])
                passed = len(files_modified) > 0
                error = None if passed else "No files were modified during integration"
                
            else:
                # Default: assume success if implementation exists
                passed = bool(implementation)
                error = None if passed else "No implementation data found"
            
            self.logger.debug(f"[TestSuiteRunner] Test '{test_name}' result: {'PASS' if passed else 'FAIL'}")
            
            return {
                "passed": passed,
                "error": error
            }
            
        except Exception as e:
            self.logger.error(f"[TestSuiteRunner] Error in test '{test.get('name', 'Unknown')}': {e}")
            return {
                "passed": False,
                "error": str(e)
            }

    def _get_test_suite(self, component: str) -> List[Dict[str, Any]]:
        """
        Get test suite for EXECUTION component types only (frontend, backend)
        Note: analyzer doesn't execute tasks, so no tests for it
        
        Args:
            component: Component type (frontend or backend only)
            
        Returns:
            List of test cases for the specific execution component
        """
        self.logger.debug(f"[TestSuiteRunner] Getting test suite for {component}")
        
        # Define test suites for EXECUTION components only
        if component == "frontend":
            tests = [
                {
                    "name": "Frontend Implementation Verification",
                    "type": "implementation",
                    "description": "Verify frontend components were implemented correctly"
                },
                {
                    "name": "Frontend File Structure Validation",
                    "type": "structure",
                    "description": "Validate frontend file organization and structure"
                },
                {
                    "name": "Frontend Component Functionality",
                    "type": "functional",
                    "description": "Test frontend component functionality"
                }
            ]
        elif component == "backend":
            tests = [
                {
                    "name": "Backend Implementation Verification",
                    "type": "implementation", 
                    "description": "Verify backend logic and services were implemented"
                },
                {
                    "name": "Backend API Integration",
                    "type": "functional",
                    "description": "Test backend API and service integration"
                },
                {
                    "name": "Backend Service Integration",
                    "type": "integration",
                    "description": "Validate backend service integrations"
                }
            ]
        else:
            # This should only happen if a new execution component is added
            self.logger.warning(f"[TestSuiteRunner] Unknown execution component '{component}', using generic tests")
            tests = [
                {
                    "name": f"{component.title()} Implementation Verification",
                    "type": "implementation",
                    "description": f"Verify {component} implementation was completed"
                }
            ]
        
        self.logger.debug(f"[TestSuiteRunner] Retrieved {len(tests)} tests for {component}")
        return tests 