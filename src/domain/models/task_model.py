"""
Task Models

Pydantic models for task orchestration and execution
"""

from typing import Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
from src.utils.exceptions_control import create_error, ValidationError

class Task(BaseModel):
    """Simplified task model with only essential fields used in practice"""
    id: str = Field(..., min_length=1, description="Unique task identifier")
    description: str = Field(..., min_length=5, description="Detailed task description")
    file_path: str = Field(..., min_length=1, description="File path for the task")
    category: str = Field(..., min_length=1, description="Task category (frontend, backend, etc.)")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="Task priority level")
    
    @field_validator("id")
    def validate_id_format(cls, v: str) -> str:
        """Validate task ID format"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task ID cannot be empty", "Task")
        return v
    
    @field_validator("description")
    def validate_description(cls, v: str) -> str:
        """Validate task description"""
        v = v.strip()
        if len(v) < 5:
            raise create_error(ValidationError, "Task description must be at least 5 characters long", "Task")
        return v
    
    @field_validator("category")
    def validate_category(cls, v: str) -> str:
        """Validate task category"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task category cannot be empty", "Task")
        return v 