"""
Configuration module for the AI Project Orchestration System
Uses Pydantic for configuration validation and type safety,
with manual loading from environment variables.
"""

import os
import ast
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.logging import setup_logger
from typing import Dict
from src.utils.exceptions_control import create_error, ValidationError
from dotenv import load_dotenv

# Setup logger first
logger = setup_logger("config")

# Load environment variables from .env file at the project root
try:
    load_dotenv()
except Exception as e:
    logger.error(f"Error loading .env file: {e}")

class BaseAppSettings(BaseSettings):
    """Base settings class with common configuration"""
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=True,
    )

class APISettings(BaseAppSettings):
    """API settings"""
    host: str = "localhost"
    port: int = 8000

    def __init__(self, **data):
        super().__init__(**data)
        self.host = os.getenv("API_HOST", self.host)
        self.port = int(os.getenv("API_PORT", self.port))
        logger.info(f"[Config] Loaded API settings - Host: {self.host}, Port: {self.port}")

class GitLabSettings(BaseAppSettings):
    """GitLab settings"""
    api_url: str = "https://gitlab.com/api/v4"
    api_token: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        self.api_url = os.getenv("GITLAB_API_URL", self.api_url)
        self.api_token = os.getenv("GITLAB_API_TOKEN", self.api_token)
        if self.api_token:
            logger.info(f"[Config] GitLab API token loaded from environment")
        else:
            logger.warning("[Config] GitLab API token not configured")

class GitHubSettings(BaseAppSettings):
    """GitHub settings"""
    api_url: str = "https://api.github.com"
    api_token: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        self.api_url = os.getenv("GITHUB_API_URL", self.api_url)
        self.api_token = os.getenv("GITHUB_API_TOKEN", self.api_token)
        if self.api_token:
            logger.info(f"[Config] GitHub API token loaded from environment")
        else:
            logger.warning("[Config] GitHub API token not configured")

class LoggingSettings(BaseAppSettings):
    """Logging settings"""
    level: str = "INFO"
    module_levels: Dict[str, str] = {
        "main": "INFO", "project": "INFO", "cli": "INFO", "evaluator": "INFO",
        "tasks": "INFO", "agent": "DEBUG", "git": "INFO", "openai": "WARNING",
        "services": "INFO", "testing": "DEBUG", "config": "WARNING",
        "exceptions": "ERROR", "mocks": "WARNING", "notification": "INFO",
        "analysis": "INFO"
    }

    def __init__(self, **data):
        super().__init__(**data)
        self.level = os.getenv('LOG_LEVEL', self.level).upper()
        
        env_module_levels = os.getenv('LOG_MODULE_LEVELS')
        if env_module_levels:
            try:
                parsed_levels = ast.literal_eval(env_module_levels)
                if isinstance(parsed_levels, dict):
                    self.module_levels.update(parsed_levels)
            except (ValueError, SyntaxError):
                logger.error("Failed to parse LOG_MODULE_LEVELS, using defaults.")
        
        logger.info(f"[Config] Logging settings loaded - Level: {self.level}")

class AgentSettings(BaseAppSettings):
    """Agent settings"""
    timeout: int = 60
    max_retries: int = 2

    def __init__(self, **data):
        super().__init__(**data)
        self.timeout = int(os.getenv('AGENT_TIMEOUT', self.timeout))
        self.max_retries = int(os.getenv('MAX_RETRIES', self.max_retries))
        logger.info(f"[Config] Agent settings loaded - Timeout: {self.timeout}s, Max retries: {self.max_retries}")

class NotificationSettings(BaseAppSettings):
    """Notification settings"""
    email: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        self.email = os.getenv('NOTIFICATION_EMAIL', self.email)
        self.smtp_server = os.getenv('SMTP_SERVER', self.smtp_server)
        self.smtp_port = int(os.getenv('SMTP_PORT', self.smtp_port))
        self.smtp_username = os.getenv('SMTP_USERNAME', self.smtp_username)
        self.smtp_password = os.getenv('SMTP_PASSWORD', self.smtp_password)

        if self.email and self.smtp_username and self.smtp_password:
            logger.info("[Config] Notification settings loaded from environment.")
        elif not self.email:
            logger.warning("[Config] NOTIFICATION_EMAIL not configured - Notifications will be disabled")
        else:
            logger.warning("[Config] SMTP credentials not fully configured - Email notifications may be disabled")

class OpenAISettings(BaseAppSettings):
    """OpenAI settings"""
    api_key: str = ""
    model: str = "gpt-5-mini"
    temperature_analysis: float = 0.2
    temperature_development: float = 0.3

    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = os.getenv("OPENAI_API_KEY", self.api_key)
        self.model = os.getenv("OPENAI_MODEL", self.model)
        self.temperature_analysis = float(os.getenv("OPENAI_TEMPERATURE_ANALYSIS", self.temperature_analysis))
        self.temperature_development = float(os.getenv("OPENAI_TEMPERATURE_DEVELOPMENT", self.temperature_development))
        if self.api_key:
            logger.info(f"[Config] OpenAI settings loaded - Model: {self.model}")
        else:
            logger.error("[Config] OpenAI API key not configured - AI functionality will be disabled")

class GitSettings(BaseAppSettings):
    """Git settings"""
    username: str = ""
    email: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        self.username = os.getenv("GIT_USERNAME", self.username)
        self.email = os.getenv("GIT_EMAIL", self.email)
        if self.username and self.email:
            logger.info(f"[Config] Git user loaded: {self.username} <{self.email}>")
        else:
            logger.warning("[Config] Git user credentials not fully configured.")

class MockSettings(BaseAppSettings):
    """Mock settings"""
    enabled: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        env_mock = os.getenv('USE_MOCKS', str(self.enabled)).lower()
        self.enabled = env_mock in ('true', '1', 'yes', 'on')
        
        if self.enabled:
            logger.info("[Config] Mock mode enabled - Using mock services")
        else:
            logger.info("[Config] Mock mode disabled - Using real services")

class Settings(BaseAppSettings):
    """Main settings class"""
    api: APISettings = Field(default_factory=APISettings)
    gitlab: GitLabSettings = Field(default_factory=GitLabSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    git: GitSettings = Field(default_factory=GitSettings)
    mock: MockSettings = Field(default_factory=MockSettings)

# Create settings instance
settings = Settings()

# Export settings instance
__all__ = ["settings"] 