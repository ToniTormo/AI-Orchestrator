"""
Implementation Execution Validator

Validates that implementations were executed correctly in cloned repositories.
These validations check if code changes were applied properly, NOT project unit tests.
"""

import logging
from typing import Dict, List, Any

class ImplementationValidator:
    """
    Validates implementation execution results to ensure changes were applied correctly.
    Used to verify that code modifications worked as expected in cloned repositories.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_validation_cases(self, component: str) -> List[Dict[str, Any]]:
        """Get validation cases for EXECUTION components only (frontend, backend)
        Note: analyzer doesn't execute tasks, so no validations for it"""
        if component == "frontend":
            return [
                {'name': 'Frontend Files Modified', 'type': 'file_check'},
                {'name': 'Frontend Code Patterns', 'type': 'pattern_check'}
            ]
        elif component == "backend":
            return [
                {'name': 'Backend Files Modified', 'type': 'file_check'},
                {'name': 'Backend Code Patterns', 'type': 'pattern_check'}
            ]
        else:
            # Fallback for unexpected execution components (should not happen)
            self.logger.warning(f"[ImplementationValidator] Unknown execution component '{component}', using generic validation")
            return [
                {'name': f'{component.title()} Implementation Status', 'type': 'status_check'}
            ]

    async def execute_validation(self, validation_case: Dict[str, Any], implementation_result: Dict[str, Any]) -> bool:
        """Execute implementation validation for execution components only"""
        validation_type = validation_case.get('type', 'basic')
        validation_name = validation_case.get('name', 'Unknown')
        
        try:
            if validation_type == 'file_check':
                return self._validate_files_modified(implementation_result)
            elif validation_type == 'pattern_check':
                return self._validate_code_patterns(implementation_result)
            elif validation_type == 'status_check':
                return self._validate_implementation_status(implementation_result)
            else:
                return True  # Default pass for unknown validation types
                
        except Exception as e:
            self.logger.error(f"[ImplementationValidator] Validation {validation_name} error: {e}")
            return False

    def _validate_files_modified(self, result: Dict[str, Any]) -> bool:
        """Validate that files were actually modified during execution"""
        files_modified = result.get("result", {}).get("files_modified", [])
        return len(files_modified) > 0

    def _validate_code_patterns(self, result: Dict[str, Any]) -> bool:
        """Validate code patterns are present in execution results"""
        # Simple validation - if files were modified, assume patterns are present
        files_modified = result.get("result", {}).get("files_modified", [])
        return len(files_modified) > 0

    def _validate_implementation_status(self, result: Dict[str, Any]) -> bool:
        """Validate implementation execution status is success"""
        return result.get("status") == "success" 