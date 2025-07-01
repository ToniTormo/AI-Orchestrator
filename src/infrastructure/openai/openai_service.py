"""
OpenAI Service

Service for interacting with OpenAI's API
"""

from typing import Any, Optional
from openai import AsyncOpenAI
from src.utils.logging import setup_logger
from src.config import settings
from src.utils.exceptions_control import create_error, OpenAIServiceError

class OpenAIService:
    """Service for interacting with OpenAI's API"""

    def __init__(self):
        """Initialize the OpenAI service"""
        self.logger = setup_logger(
            "openai.service",
            settings.logging.module_levels.get("openai", settings.logging.level)
        )
        
        if not settings.openai.api_key:
            raise create_error(OpenAIServiceError, "OpenAI API key not found in configuration", "OpenAIService")
        
        try:
            self.client = AsyncOpenAI(api_key=settings.openai.api_key)
            self.default_model = settings.openai.model
            
            self.logger.info("[OpenAI] Service initialized with configured API key")
            
        except Exception as e:
            raise create_error(OpenAIServiceError, f"Failed to initialize OpenAI service: {str(e)}", "OpenAIService")

    async def create_completion(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Create a completion using OpenAI's API
        
        Args:
            prompt: The input prompt text
            model: Model to use for completion (defaults to config value)
            temperature: Sampling temperature (defaults to config value)
            max_tokens: Maximum number of tokens to generate (optional)
            
        Returns:
            OpenAI API response
        """
        if not prompt or not prompt.strip():
            raise create_error(OpenAIServiceError, "Prompt cannot be empty", "OpenAIService")
            
        try:
            # Use config defaults if not provided
            model = model or self.default_model
            temperature = temperature if temperature is not None else 0.2
            max_tokens = max_tokens if max_tokens is not None else 4000
            
            self.logger.debug(f"[OpenAI] Creating completion with model: {model}")
            
            # Use chat.completions for modern models, legacy completions for older ones
            if model.startswith(('gpt-3.5', 'gpt-4')):
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = await self.client.completions.create(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            self.logger.debug("[OpenAI] Completion created successfully")
            return response
            
        except Exception as e:
            raise create_error(OpenAIServiceError, f"Failed to create completion: {str(e)}", "OpenAIService") 