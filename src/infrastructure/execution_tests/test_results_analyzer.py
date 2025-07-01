"""
Test Results Analyzer

Handles analysis of test execution results and generates insights.
"""

from typing import Dict, List, Any
from src.utils.logging import setup_logger
from src.config import settings

class TestResultsAnalyzer:
    """
    Analyzes test execution results and generates insights and recommendations.
    """
    
    def __init__(self):
        """Initialize the test results analyzer"""
        self.logger = setup_logger(
            "execution_tests.results_analyzer", 
            settings.logging.module_levels.get("execution_tests", settings.logging.level)
        )
    
    async def analyze_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test results and generate insights
        
        Args:
            results: Test results to analyze
            
        Returns:
            Analysis results with status, pass rates, and recommendations
        """
        try:
            self.logger.info("[TestResultsAnalyzer] Starting test results analysis")
            analysis = {
                "overall_status": "passed",
                "component_status": {},
                "recommendations": []
            }
            
            # Analyze each component
            for component, component_results in results.items():
                status = "passed" if component_results["failed"] == 0 else "failed"
                pass_rate = component_results["passed"] / component_results["total"] if component_results["total"] > 0 else 0
                
                analysis["component_status"][component] = {
                    "status": status,
                    "pass_rate": pass_rate
                }
                
                # Add recommendations for failed tests
                if status == "failed":
                    for test in component_results["failed_tests"]:
                        recommendation = {
                            "component": component,
                            "test": test["name"],
                            "suggestion": f"Review and fix {test['name']} in {component}"
                        }
                        analysis["recommendations"].append(recommendation)
                        self.logger.warning(f"[TestResultsAnalyzer] Added recommendation for failed test: {test['name']}")
            
            # Set overall status
            if any(status["status"] == "failed" 
                  for status in analysis["component_status"].values()):
                analysis["overall_status"] = "failed"
            
            self.logger.info(f"[TestResultsAnalyzer] Analysis completed. Overall status: {analysis['overall_status']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"[TestResultsAnalyzer] Error analyzing test results: {e}")
            return {
                "overall_status": "error",
                "error": str(e)
            } 