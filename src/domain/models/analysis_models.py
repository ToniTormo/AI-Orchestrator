"""
Analysis Models

Pydantic models for analysis operations validation
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from src.utils.exceptions_control import create_error, ValidationError

class TechStackAnalysisInput(BaseModel):
    """Model for validating tech stack analysis input"""
    repo_path: str = Field(..., description="Path to repository")
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        """Validate repository path is not empty"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Repository path cannot be empty", "TechStackAnalysisInput")
        return v

class AnalysisTask(BaseModel):
    """Model for validating analysis task output"""
    id: str = Field(..., min_length=1, description="Unique task identifier")
    file_path: str = Field(..., min_length=1, description="Path to the file to be modified")
    specific_changes: str = Field(..., min_length=10, description="Specific changes to be made to the file")
    
    @field_validator('id')
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID is not empty"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Task ID cannot be empty", "AnalysisTask")
        return v
    
    @field_validator('file_path')
    def validate_file_path(cls, v: str) -> str:
        """Validate file path is not empty"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "File path cannot be empty", "AnalysisTask")
        return v
    
    @field_validator('specific_changes')
    def validate_specific_changes(cls, v: str) -> str:
        """Validate specific changes description"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Specific changes cannot be empty", "AnalysisTask")
        if len(v) < 10:
            raise create_error(ValidationError, "Specific changes description too short (min 10 characters)", "AnalysisTask")
        return v

class AgentAnalyzerInput(BaseModel):
    """Model for validating AgentAnalyzer input parameters"""
    description: str = Field(..., min_length=1, description="Project description")
    repo_path: str = Field(..., min_length=1, description="Repository path")
    structure: Dict[str, Any] = Field(..., description="Repository structure")
    technologies: Dict[str, Any] = Field(..., description="Technologies used")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Initial confidence score")
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        """Validate project description"""
        v = v.strip()
        if len(v) < 1:
            raise create_error(ValidationError, "Description cannot be empty", "AgentAnalyzerInput")
        return v
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        """Validate repository path"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Repository path cannot be empty", "AgentAnalyzerInput")
        return v

class AgentAnalyzerOutput(BaseModel):
    """Model for validating AgentAnalyzer output"""
    viability_score: int = Field(..., ge=0, le=100, description="Project viability score from 0 to 100")
    tasks: List[AnalysisTask] = Field(default_factory=list, description="List of analysis tasks")

