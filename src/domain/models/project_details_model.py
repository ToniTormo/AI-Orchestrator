"""
Project Models

Models for representing project information and details
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, HttpUrl, EmailStr
from src.utils.exceptions_control import create_error, ProjectError, ValidationError

class ContextCreationInput(BaseModel):
    """
    Model for validating CLI context creation parameters
    """
    repo_url: HttpUrl = Field(..., description="URL of the repository to clone")
    branch: str = Field(..., min_length=1, description="Branch to merge into")
    description: str = Field(..., min_length=1, description="Description of the requested changes")
    email: EmailStr = Field(..., description="E-mail address for review notifications")
    repos_path: Optional[str] = Field(None, description="Optional custom path for repositories")
    
    @field_validator('branch')
    def validate_branch(cls, v: str) -> str:
        """Validate branch name"""
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Branch name cannot be empty", "ContextCreationInput")
        return v
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        """Validate description"""
        v = v.strip()
        if len(v) < 1:
            raise create_error(ValidationError, "Description must be at least 1 characters long", "ContextCreationInput")
        return v

class RepositoryAnalysisResult(BaseModel):
    """
    Model for validating repository analysis results
    """
    repo_path: str = Field(..., description="Path to the repository")
    structure: Dict[str, Any] = Field(..., description="Repository structure information")
    complexity_score: float = Field(..., ge=0, le=1, description="Complexity score between 0-1")
    technologies: Dict[str, List[str]] = Field(..., description="Detected technologies by category")
    estimated_hours: int = Field(..., ge=8, le=200, description="Estimated development hours")
    
    @field_validator('structure')
    def validate_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate repository structure"""
        if not v:
            raise create_error(ValidationError, "Repository structure cannot be empty", "RepositoryAnalysisResult")
        
        required_fields = ['name', 'files', 'directories', 'total_files', 'total_directories']
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise create_error(ValidationError, f"Repository structure missing required fields: {missing_fields}", "RepositoryAnalysisResult")
        
        if not v.get('name'):
            raise create_error(ValidationError, "Repository name cannot be empty", "RepositoryAnalysisResult")
        
        return v
    
    @field_validator('technologies')
    def validate_technologies(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate technologies"""
        if not v:
            raise create_error(ValidationError, "Technologies cannot be empty", "RepositoryAnalysisResult")
        return v

class ViabilityAnalysisResult(BaseModel):
    """
    Model for validating viability analysis results
    """
    is_viable: bool = Field(..., description="Whether the project is viable")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score between 0-100")
    reasoning: Optional[str] = Field(None, description="Reasoning for the viability assessment")
    tasks_steps: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of task steps from AI analysis")
    
    @field_validator('confidence_score')
    def validate_confidence_score(cls, v: float) -> float:
        """Validate confidence score range"""
        if not 0 <= v <= 100:
            raise create_error(ValidationError, f"Confidence score must be between 0-100, got {v}", "ViabilityAnalysisResult")
        return v

class TaskExecutionResults(BaseModel):
    """
    Model for validating task execution results
    """
    tasks_completed: int = Field(..., ge=0, description="Number of tasks completed")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Test execution results")
    changes_summary: str = Field(..., min_length=1, description="Summary of changes made")
    
    @field_validator('test_results')
    def validate_test_results(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results structure"""
        if not v:
            raise create_error(ValidationError, "Test results cannot be empty", "TaskExecutionResults")
        
        # Ensure all_passed field exists
        if 'all_passed' not in v:
            raise create_error(ValidationError, "Test results must include 'all_passed' field", "TaskExecutionResults")
        
        return v
    
    @field_validator('success_rate')
    def validate_success_rate(cls, v: float) -> float:
        """Validate success rate range"""
        if not 0 <= v <= 100:
            raise create_error(ValidationError, f"Success rate must be between 0-100, got {v}", "TaskExecutionResults")
        return v

 