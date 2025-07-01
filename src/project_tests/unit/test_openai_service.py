"""
Unit tests for OpenAIService

Tests for critical OpenAI API integration functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.infrastructure.openai.openai_service import OpenAIService
from src.utils.exceptions_control import OpenAIServiceError
from src.config import settings
# ==================== FIXTURES ====================

@pytest.fixture
def openai_service():
    """Create OpenAIService instance for testing."""
    
    with patch('src.infrastructure.openai.openai_service.settings') as mock_settings:
        mock_settings.openai.api_key = "test-api-key"
        mock_settings.openai.model = settings.openai.model  # Use actual configured model
        mock_settings.openai.temperature_analysis = 0.2
        mock_settings.openai.temperature_development = 0.3
        mock_settings.logging.module_levels = MagicMock()
        mock_settings.logging.module_levels.get.return_value = "INFO"
        
        with patch('src.infrastructure.openai.openai_service.AsyncOpenAI'):
            with patch('src.infrastructure.openai.openai_service.setup_logger') as mock_logger:
                mock_logger.return_value = Mock()
                
                service = OpenAIService()
                service.client = AsyncMock()
                # Store the model for test assertions
                service._test_model = settings.openai.model
                return service

# ==================== TESTS ====================

@pytest.mark.unit
class TestOpenAIService:
    """Test OpenAIService class - critical functionality only"""

    def test_openai_service_initialization_success(self):
        """Test successful OpenAIService initialization with API key."""

        with patch('src.infrastructure.openai.openai_service.settings') as mock_settings:
            mock_settings.openai.api_key = "test-api-key"
            mock_settings.openai.model = settings.openai.model
            mock_settings.openai.temperature_analysis = 0.2
            mock_settings.openai.temperature_development = 0.3
            mock_settings.logging.module_levels = MagicMock()
            mock_settings.logging.module_levels.get.return_value = "INFO"
            
            with patch('src.infrastructure.openai.openai_service.AsyncOpenAI') as mock_openai:
                with patch('src.infrastructure.openai.openai_service.setup_logger') as mock_logger:
                    mock_logger.return_value = Mock()
                    
                    service = OpenAIService()
                    
                    assert service is not None
                    assert service.default_model == settings.openai.model
                    mock_openai.assert_called_once_with(api_key="test-api-key")

    def test_openai_service_initialization_no_api_key(self):
        """Test OpenAIService initialization fails without API key."""
        with patch('src.infrastructure.openai.openai_service.settings') as mock_settings:
            mock_settings.openai.api_key = ""
            mock_settings.logging.module_levels = MagicMock()
            mock_settings.logging.module_levels.get.return_value = "INFO"
            
            with patch('src.infrastructure.openai.openai_service.setup_logger') as mock_logger:
                mock_logger.return_value = Mock()
                
                with pytest.raises(OpenAIServiceError) as exc_info:
                    OpenAIService()
                
                assert "OpenAI API key not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_completion_chat_model_success(self, openai_service):
        """Test successful completion creation with chat model."""
        prompt = "Test prompt"
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        
        openai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await openai_service.create_completion(prompt)
        
        assert result == mock_response

        openai_service.client.chat.completions.create.assert_called_once_with(
            model=settings.openai.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4000
        )

    @pytest.mark.asyncio
    async def test_create_completion_empty_prompt(self, openai_service):
        """Test completion creation with empty prompt."""
        empty_prompts = ["", "   ", None]
        
        for prompt in empty_prompts:
            with pytest.raises(OpenAIServiceError) as exc_info:
                await openai_service.create_completion(prompt)
            
            assert "Prompt cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_completion_api_failure(self, openai_service):
        """Test completion creation when API call fails."""
        prompt = "Test prompt"
        
        # Mock API failure
        openai_service.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API request failed")
        )
        
        with pytest.raises(OpenAIServiceError) as exc_info:
            await openai_service.create_completion(prompt)
        
        assert "Failed to create completion" in str(exc_info.value) 