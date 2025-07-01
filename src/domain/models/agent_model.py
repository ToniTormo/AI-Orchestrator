"""
Agent Models

Models for AI agents and their tasks
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from src.utils.exceptions_control import create_error, ValidationError

class AgentType(str, Enum):
    """Types of AI agents"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    ANALYZER = "analyzer"

class AgentTask(BaseModel):
    """Task to be executed by an agent"""
    task_id: str = Field(..., min_length=1, description="Unique task identifier")
    agent_type: AgentType
    description: str = Field(..., min_length=5, max_length=15000, description="Task description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Task execution context")
    
    model_config = ConfigDict(use_enum_values=True)
    
    @field_validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID is not empty and properly formatted"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task ID cannot be empty", "AgentTask")
        return v
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        """Validate task description"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task description cannot be empty", "AgentTask")
        if len(v) < 5:
            raise create_error(ValidationError, "Task description too short (min 5 characters)", "AgentTask")
        return v
    
    @field_validator('context')
    def validate_context(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context dictionary"""
        if not isinstance(v, dict):
            raise create_error(ValidationError, "Context must be a dictionary", "AgentTask")
        return v

class AgentResult(BaseModel):
    """Result of an agent task execution"""
    task_id: str = Field(..., min_length=1, description="Task identifier")
    success: bool = Field(..., description="Whether the task was successful")
    output: str = Field(..., min_length=1, description="Task output or result")
    error: Optional[str] = Field(None, max_length=10000, description="Error message if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    completed_at: datetime = Field(default_factory=datetime.now, description="Completion timestamp")
    
    @field_validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID matches the associated task"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task ID cannot be empty", "AgentResult")
        return v
    
    @field_validator('output')
    def validate_output(cls, v: str) -> str:
        """Validate output is meaningful"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Output cannot be empty", "AgentResult")
        return v
    
    @field_validator('error')
    def validate_error(cls, v: Optional[str]) -> Optional[str]:
        """Validate error message format"""
        if v is not None:
            v = v.strip()
            if not v:
                return None  # Convert empty string to None
        return v
    
    @field_validator('metadata')
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata dictionary"""
        if not isinstance(v, dict):
            raise create_error(ValidationError, "Metadata must be a dictionary", "AgentResult")
        return v

class AgentStatus(BaseModel):
    """Model for agent status information"""
    registered_at: datetime = Field(..., description="Agent registration timestamp")
    status: str = Field(..., description="Current agent status")
    last_health_check: datetime = Field(..., description="Last health check timestamp")
    healthy: Optional[bool] = Field(None, description="Health check result")
    error: Optional[str] = Field(None, max_length=10000, description="Error message if any")
    shutdown_at: Optional[datetime] = Field(None, description="Shutdown timestamp")
    
    @field_validator('status')
    def validate_status(cls, v: str) -> str:
        """Validate agent status is one of allowed values"""
        v = v.strip().lower()
        allowed_statuses = {'available', 'error', 'shutdown', 'unknown'}
        if v not in allowed_statuses:
            raise create_error(ValidationError, f"Invalid status '{v}'. Must be one of: {allowed_statuses}", "AgentStatus")
        return v
    
    @field_validator('error')
    def validate_error(cls, v: Optional[str]) -> Optional[str]:
        """Validate error message"""
        if v is not None:
            v = v.strip()
            if not v:
                return None  # Convert empty string to None
        return v
    
    @field_validator('last_health_check')
    def validate_health_check_time(cls, v: datetime) -> datetime:
        """Validate health check timestamp is not in the future"""
        if v > datetime.now():
            raise create_error(ValidationError, "Health check timestamp cannot be in the future", "AgentStatus")
        return v
    
    @field_validator('registered_at')
    def validate_registered_at(cls, v: datetime) -> datetime:
        """Validate registration timestamp is not in the future"""
        if v > datetime.now():
            raise create_error(ValidationError, "Registration timestamp cannot be in the future", "AgentStatus")
        return v 