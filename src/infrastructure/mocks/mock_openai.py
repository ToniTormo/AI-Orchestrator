"""
Mock OpenAI Service

Provides a mock implementation of the OpenAI service for testing and development
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from types import SimpleNamespace

from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, MockServiceError
from src.config import settings
from .mock_responses import MOCK_RESPONSES

class MockOpenAIService:
    """Mock implementation of OpenAI service"""
    
    def __init__(self):
        """Initialize the mock service"""
        self.logger = setup_logger(
            "mocks.openai", 
            settings.logging.module_levels.get("mocks", settings.logging.level)
        )
        
        self.logger.info("[MockOpenAI] Initializing mock OpenAI service")
        self._responses = MOCK_RESPONSES
        self._call_count = 0
        self.logger.info("[MockOpenAI] Mock service initialized successfully")

    async def create_completion(
        self,
        prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs
    ) -> Any:
        """
        Mock implementation of completion
        
        Args:
            prompt: The prompt text
            model: Model to use (ignored in mock)
            temperature: Sampling temperature (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)
            
        Returns:
            Object mimicking OpenAI response structure with attributes
        """
        if not prompt or not prompt.strip():
            raise create_error(MockServiceError, "Prompt cannot be empty", "MockOpenAIService")
            
        try:
            self._call_count += 1
            self.logger.info(f"[MockOpenAI] Creating completion (call #{self._call_count})")
            
            response_type = self._determine_response_type(prompt)
            response_content = self._get_mock_response(response_type, prompt)
            
            # Create objects with attributes like the real OpenAI library
            message = SimpleNamespace(
                role="assistant",
                content=json.dumps(response_content)
            )
            
            choice = SimpleNamespace(
                index=0,
                message=message,
                finish_reason="stop"
            )
            
            usage = SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
            
            response = SimpleNamespace(
                id=f"mock-{datetime.now().timestamp()}",
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=model,
                choices=[choice],
                usage=usage
            )
            
            return response
            
        except Exception as e:
            raise create_error(MockServiceError, f"Error creating mock completion: {str(e)}", "MockOpenAIService")

    def get_call_count(self) -> int:
        """Get the number of API calls made"""
        return self._call_count
    
    def reset_call_count(self) -> None:
        """Reset the API call counter"""
        self._call_count = 0
        
    def _determine_response_type(self, prompt: str) -> str:
        """Determine which mock response to use based on the prompt content"""
        prompt_lower = prompt.lower()
        
        if "analyze the following project" in prompt_lower:
            return "analyze_project"
        elif "which files are most relevant" in prompt_lower:
            return "filter_files"
        else:
            return "analyze_project"  # Default response
            
    def _get_mock_response(self, response_type: str, prompt: str) -> Dict[str, Any]:
        """Get the appropriate mock response and handle dynamic content"""
        response_content = self._responses.get(response_type)
        if not response_content:
            raise create_error(MockServiceError, f"No mock response found for type: {response_type}", "MockOpenAIService")

        # Handle dynamic file filtering
        if response_type == "filter_files":
            relevant_files_indices = self._get_dynamic_file_indices(prompt)
            response_content = response_content.copy()  # Don't modify the original
            response_content['relevant_files'] = relevant_files_indices
            
        return response_content

    def _get_dynamic_file_indices(self, prompt: str) -> List[int]:
        """Dynamically generate file indices based on the prompt content."""
        try:
            if "And these code files:" in prompt:
                files_section = prompt.split("And these code files:")[1].split("Which files are most relevant")[0].strip()
                
                file_entries = [
                    line.strip() for line in files_section.split("\n") 
                    if line.strip() and not line.startswith("```")
                ]
                
                file_count = len(file_entries)
                self.logger.debug(f"[MockOpenAI] Detected {file_count} files in prompt for filtering")
                return list(range(file_count))
            else:
                self.logger.debug("[MockOpenAI] Could not detect files for filtering, returning default [0]")
                return [0]
                
        except Exception as e:
            self.logger.warning(f"[MockOpenAI] Error parsing file count from prompt: {str(e)}, returning [0]")
            return [0] 
        